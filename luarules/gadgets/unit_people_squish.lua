local gadget = gadget ---@type Gadget

function gadget:GetInfo()
	return {
		name = "People Squish",
		desc = "True-scale infantry get run over by moving enemy vehicles and bots",
		author = "bar-people",
		date = "2026",
		license = "GNU GPL, v2 or later",
		layer = 0,
		enabled = true,
	}
end

if not gadgetHandler:IsSyncedCode() then
	return
end

local CHECK_EVERY = 3 -- frames
local MIN_CRUSHER_MASS = 100
local MIN_SPEED = 0.4 -- elmos per frame

local spGetUnitPosition = Spring.GetUnitPosition
local spGetUnitVelocity = Spring.GetUnitVelocity
local spGetUnitsInCylinder = Spring.GetUnitsInCylinder
local spGetUnitDefID = Spring.GetUnitDefID
local spGetUnitAllyTeam = Spring.GetUnitAllyTeam
local spGetUnitIsDead = Spring.GetUnitIsDead
local spGetUnitTransporter = Spring.GetUnitTransporter
local spDestroyUnit = Spring.DestroyUnit

local peopleDefs = {}
local crusherReach = {} -- unitDefID -> distance from crusher centre at which a person is under it
local maxReach = 0

for unitDefID, ud in pairs(UnitDefs) do
	if ud.customParams.people_soldier then
		peopleDefs[unitDefID] = true
	elseif ud.canMove and not ud.canFly and not ud.isBuilding and (ud.mass or 0) >= MIN_CRUSHER_MASS then
		local reach = math.max(ud.xsize, ud.zsize) * 4 + 4 -- half footprint (8 elmos per square) plus contact
		crusherReach[unitDefID] = reach
		maxReach = math.max(maxReach, reach)
	end
end

local people = {}

function gadget:UnitCreated(unitID, unitDefID)
	if peopleDefs[unitDefID] then
		people[unitID] = true
	end
end

function gadget:UnitDestroyed(unitID)
	people[unitID] = nil
end

function gadget:Initialize()
	if not next(peopleDefs) then
		gadgetHandler:RemoveGadget(self)
		return
	end
	for _, unitID in ipairs(Spring.GetAllUnits()) do
		gadget:UnitCreated(unitID, spGetUnitDefID(unitID))
	end
end

local function findCrusher(unitID)
	if spGetUnitTransporter(unitID) then
		return nil
	end
	local x, _, z = spGetUnitPosition(unitID)
	if not x then
		return nil
	end
	local allyTeam = spGetUnitAllyTeam(unitID)
	for _, otherID in ipairs(spGetUnitsInCylinder(x, z, maxReach)) do
		local reach = crusherReach[spGetUnitDefID(otherID)]
		if reach and spGetUnitAllyTeam(otherID) ~= allyTeam then
			local ox, _, oz = spGetUnitPosition(otherID)
			local dx, dz = x - ox, z - oz
			if dx * dx + dz * dz < reach * reach then
				local vx, _, vz, speed = spGetUnitVelocity(otherID)
				-- must be driving into the person, not just parked next to them
				if speed and speed > MIN_SPEED and (vx * dx + vz * dz) > 0 then
					return otherID
				end
			end
		end
	end
	return nil
end

function gadget:GameFrame(n)
	if n % CHECK_EVERY ~= 0 then
		return
	end
	local squished
	for unitID in pairs(people) do
		local crusherID = findCrusher(unitID)
		if crusherID then
			squished = squished or {}
			squished[unitID] = crusherID
		end
	end
	if squished then
		for unitID, crusherID in pairs(squished) do
			if not spGetUnitIsDead(unitID) then
				spDestroyUnit(unitID, false, false, crusherID)
			end
		end
	end
end
