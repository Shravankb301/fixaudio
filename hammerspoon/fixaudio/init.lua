-- fixaudio - keyboard volume control for monitors macOS won't let you control,
-- plus fast output-device switching.
--
-- Add to ~/.hammerspoon/init.lua:
--
--     require("fixaudio").start()
--
-- Optionally with overrides:
--
--     require("fixaudio").start({ step = 4, switchHotkey = {{"ctrl"}, "F1"} })

local M = {}

M.config = {
  -- Volume change per key press, out of 100.
  step = 6,
  -- Hotkey that cycles the audio output device. Set to false to disable.
  switchHotkey = { { "cmd", "alt", "ctrl" }, "A" },
  -- Show the menubar output switcher.
  menubar = true,
  -- Show an on-screen HUD on volume and device changes.
  hud = true,
}

-- --- locating the CLI --------------------------------------------------------

-- hs.task needs an absolute path, and Hammerspoon doesn't inherit a login shell
-- PATH, so look in the places the installer might have put things.
local SEARCH_PATHS = {
  "/usr/local/bin/", "/opt/homebrew/bin/",
  os.getenv("HOME") .. "/.local/bin/",
}

local binCache = {}

function M.bin(name)
  if binCache[name] then return binCache[name] end
  for _, dir in ipairs(SEARCH_PATHS) do
    local p = dir .. name
    if hs.fs.attributes(p) then
      binCache[name] = p
      return p
    end
  end
  return nil
end

M.env = {
  PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
  HOME = os.getenv("HOME"),
}

-- Run a CLI subcommand without blocking; cb receives trimmed stdout.
function M.run(name, args, cb)
  local path = M.bin(name)
  if not path then
    hs.printf("fixaudio: cannot find '%s' on disk; is it installed?", name)
    if cb then cb(nil) end
    return
  end
  local t = hs.task.new(path, function(_, stdout, _)
    if cb then cb((stdout or ""):gsub("%s+$", "")) end
  end, args)
  t:setEnvironment(M.env)
  t:start()
end

-- --- shared HUD --------------------------------------------------------------

local lastAlert = nil

function M.hud(text)
  if not M.config.hud then return end
  if lastAlert then hs.alert.closeSpecific(lastAlert, 0) end
  lastAlert = hs.alert.show(text, {
    strokeWidth = 0,
    fillColor = { white = 0, alpha = 0.75 },
    textSize = 20,
    radius = 10,
  }, 0.9)
end

-- --- route cache -------------------------------------------------------------
--
-- Deciding whether the current output is a DDC-controllable display means
-- shelling out, which is far too slow to do on every keypress. So we resolve it
-- once per output-device change and cache the answer.

M.route = "mac"

function M.refreshRoute(cb)
  M.run("ddcvol", { "route" }, function(out)
    M.route = (out == "ddc") and "ddc" or "mac"
    if cb then cb(M.route) end
  end)
end

function M.onDDC() return M.route == "ddc" end

function M.currentOutputName()
  local d = hs.audiodevice.defaultOutputDevice()
  return d and d:name() or "?"
end

-- --- output-change fanout ----------------------------------------------------
--
-- hs.audiodevice.watcher is a singleton with a single callback, so this module
-- owns it and fans out. Submodules must register here rather than calling
-- setCallback themselves, which would silently replace this handler.

M.subscribers = {}

function M.onOutputChange(fn) table.insert(M.subscribers, fn) end

local function outputChanged()
  M.refreshRoute(function()
    -- Monitors sit at whatever their own buttons last left them at, so put our
    -- cached level back.
    if M.onDDC() then M.run("ddcvol", { "sync" }, nil) end
  end)

  for _, fn in ipairs(M.subscribers) do pcall(fn) end
end

-- --- lifecycle ---------------------------------------------------------------

function M.start(opts)
  for k, v in pairs(opts or {}) do M.config[k] = v end

  if not M.bin("ddcvol") then
    hs.alert.show("fixaudio: ddcvol not found — run the installer")
    return M
  end

  M.volume = require("fixaudio.volume").start(M)
  M.switcher = require("fixaudio.switcher").start(M)

  M.audioWatcher = hs.audiodevice.watcher
  M.audioWatcher.setCallback(function(arg)
    -- The device isn't fully settled the instant the notification fires.
    if arg == "dOut" then hs.timer.doAfter(0.6, outputChanged) end
  end)
  M.audioWatcher.start()

  M.wakeWatcher = hs.caffeinate.watcher.new(function(ev)
    if ev == hs.caffeinate.watcher.systemDidWake
      or ev == hs.caffeinate.watcher.screensDidWake then
      -- Displays take a while to come back and accept DDC after waking.
      hs.timer.doAfter(3, outputChanged)
    end
  end)
  M.wakeWatcher:start()

  M.refreshRoute()
  return M
end

return M
