-- Output-device switching: a cycle hotkey and a menubar picker.
--
-- Switching is done natively rather than by shelling out, so it's instant.

local M = {}
local core

local function shortName(name)
  local aliases = {
    ["Mac mini Speakers"] = "Mac mini",
    ["MacBook Pro Speakers"] = "MacBook",
    ["External Headphones"] = "Headphones",
  }
  if aliases[name] then return aliases[name] end
  if #name > 12 then return name:sub(1, 11) .. "…" end
  return name
end

-- Sorted so the cycle order is stable between calls.
local function outputs()
  local devices = hs.audiodevice.allOutputDevices()
  table.sort(devices, function(a, b) return a:name() < b:name() end)
  return devices
end

local function switchTo(device)
  if not device then return end

  device:setDefaultOutputDevice()
  -- Keep alert and UI sounds on the same device as everything else.
  if device.setDefaultEffectDevice then
    pcall(function() device:setDefaultEffectDevice() end)
  end

  core.hud("🔈  " .. device:name())
  M.updateTitle()
  -- The core watcher also fires, which refreshes the route and re-syncs volume.
end

function M.cycle()
  local devices = outputs()
  if #devices == 0 then return end

  local cur = core.currentOutputName()
  local idx = 1
  for i, d in ipairs(devices) do
    if d:name() == cur then
      idx = (i % #devices) + 1
      break
    end
  end

  switchTo(devices[idx])
end

function M.updateTitle()
  if M.menu then
    M.menu:setTitle("🔈 " .. shortName(core.currentOutputName()))
  end
end

local function buildMenu()
  local cur = core.currentOutputName()
  local items = {}

  for _, d in ipairs(outputs()) do
    local name = d:name()
    table.insert(items, {
      title = name,
      checked = (name == cur),
      fn = function() switchTo(hs.audiodevice.findOutputByName(name)) end,
    })
  end

  table.insert(items, { title = "-" })
  table.insert(items, {
    title = "Re-sync monitor volume",
    disabled = not core.onDDC(),
    fn = function() core.run("ddcvol", { "sync" }, nil) end,
  })

  return items
end

function M.start(coreModule)
  core = coreModule

  local hk = core.config.switchHotkey
  if hk then
    M.hotkey = hs.hotkey.bind(hk[1], hk[2], M.cycle)
  end

  if core.config.menubar then
    M.menu = hs.menubar.new()
    M.menu:setMenu(buildMenu)
    M.updateTitle()
    -- Reflect changes made elsewhere (Control Center, plugging in headphones).
    core.onOutputChange(M.updateTitle)
  end

  return M
end

return M
