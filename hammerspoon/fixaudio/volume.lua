-- Media-key interception.
--
-- When the output is a DDC display we swallow the key and translate it into a
-- DDC write. Otherwise we let it through and macOS behaves exactly as always.

local M = {}
local core

-- --- serialised command queue ------------------------------------------------
--
-- Holding a volume key fires faster than a shell round-trip completes, so we
-- coalesce: at most one ddcvol runs at a time, and repeats arriving while one is
-- in flight accumulate into a single follow-up call.

local inFlight = false
local pendingDelta = 0
local pendingMute = false

local function levelHUD(text)
  local n = tonumber(text)
  if n then
    local filled = math.floor(n / 10 + 0.5)
    core.hud(string.format("%s  %s%s  %d",
      n == 0 and "🔇" or "🔊",
      string.rep("█", filled),
      string.rep("░", 10 - filled),
      n))
  elseif text == "muted" then
    core.hud("🔇  muted")
  elseif text and text ~= "" then
    core.hud("🔊  " .. text)
  end
end

local function pump()
  if inFlight then return end

  local args
  if pendingMute then
    pendingMute = false
    args = { "mute" }
  elseif pendingDelta ~= 0 then
    local d = pendingDelta
    pendingDelta = 0
    args = d > 0 and { "up", tostring(d) } or { "down", tostring(-d) }
  else
    return
  end

  inFlight = true
  core.run("ddcvol", args, function(out)
    inFlight = false
    levelHUD(out)
    pump()
  end)
end

-- --- key tap -----------------------------------------------------------------

function M.start(coreModule)
  core = coreModule

  M.tap = hs.eventtap.new({ hs.eventtap.event.types.systemDefined }, function(event)
    local data = event:systemKey()
    if not data or not data.down then return false end

    local key = data.key
    if key ~= "SOUND_UP" and key ~= "SOUND_DOWN" and key ~= "MUTE" then
      return false
    end

    -- Not on a DDC display: hand the key back to macOS untouched.
    if not core.onDDC() then return false end

    if key == "MUTE" then
      pendingMute = true
    else
      local step = core.config.step
      pendingDelta = pendingDelta + (key == "SOUND_UP" and step or -step)
    end
    pump()

    return true   -- swallow it, so macOS doesn't also beep at us
  end)

  M.tap:start()

  if not hs.accessibilityState() then
    hs.alert.show("fixaudio: grant Hammerspoon Accessibility access\n"
      .. "System Settings → Privacy & Security → Accessibility", 6)
  end

  return M
end

return M
