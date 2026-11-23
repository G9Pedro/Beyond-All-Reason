-- Shared animation script for the true-scale infantry (armsoldier, corsoldier).
-- Pieces come from tools/people_soldiers/build_people.py.

local base, pelvis, torso, head = piece("base", "pelvis", "torso", "head")
local aim, rarm, larm, rifle, flare = piece("aim", "rarm", "larm", "rifle", "flare")
local rthigh, rshin, lthigh, lshin = piece("rthigh", "rshin", "lthigh", "lshin")

local rad = math.rad
local SIG_WALK = 1
local SIG_AIM = 2
local SIG_RESTORE = 4

local isAiming = false

local function walk()
	Signal(SIG_WALK)
	SetSignalMask(SIG_WALK)
	local legSpeed = rad(260)
	local kneeSpeed = rad(320)
	while true do
		Turn(rthigh, x_axis, rad(-32), legSpeed)
		Turn(rshin, x_axis, rad(10), kneeSpeed)
		Turn(lthigh, x_axis, rad(28), legSpeed)
		Turn(lshin, x_axis, rad(45), kneeSpeed)
		Move(pelvis, y_axis, 0.25, 4)
		if not isAiming then
			Turn(torso, y_axis, rad(4), rad(30))
		end
		WaitForTurn(rthigh, x_axis)
		Move(pelvis, y_axis, 0, 4)

		Turn(lthigh, x_axis, rad(-32), legSpeed)
		Turn(lshin, x_axis, rad(10), kneeSpeed)
		Turn(rthigh, x_axis, rad(28), legSpeed)
		Turn(rshin, x_axis, rad(45), kneeSpeed)
		Move(pelvis, y_axis, 0.25, 4)
		if not isAiming then
			Turn(torso, y_axis, rad(-4), rad(30))
		end
		WaitForTurn(lthigh, x_axis)
		Move(pelvis, y_axis, 0, 4)
	end
end

local function stand()
	Signal(SIG_WALK)
	local s = rad(200)
	Turn(rthigh, x_axis, 0, s)
	Turn(rshin, x_axis, 0, s)
	Turn(lthigh, x_axis, 0, s)
	Turn(lshin, x_axis, 0, s)
	Move(pelvis, y_axis, 0, 4)
	if not isAiming then
		Turn(torso, y_axis, 0, rad(60))
	end
end

local function restoreAim()
	Signal(SIG_RESTORE)
	SetSignalMask(SIG_RESTORE)
	Sleep(2500)
	isAiming = false
	Turn(torso, y_axis, 0, rad(120))
	-- rifle held at low ready
	Turn(aim, x_axis, rad(25), rad(90))
	Turn(head, y_axis, 0, rad(120))
end

function script.Create()
	Turn(aim, x_axis, rad(25))
end

function script.StartMoving()
	StartThread(walk)
end

function script.StopMoving()
	StartThread(stand)
end

function script.AimFromWeapon1()
	return aim
end

function script.QueryWeapon1()
	return flare
end

function script.AimWeapon1(heading, pitch)
	Signal(SIG_AIM)
	SetSignalMask(SIG_AIM)
	isAiming = true
	Turn(torso, y_axis, heading, rad(360))
	Turn(aim, x_axis, -pitch, rad(240))
	WaitForTurn(torso, y_axis)
	WaitForTurn(aim, x_axis)
	StartThread(restoreAim)
	return true
end

function script.FireWeapon1()
	-- tiny recoil
	Move(rifle, z_axis, -0.3)
	Move(rifle, z_axis, 0, 6)
end

function script.Killed(recentDamage, maxHealth)
	Signal(SIG_WALK)
	Signal(SIG_AIM)
	Signal(SIG_RESTORE)
	-- crumple: knees give, then fall flat
	Turn(rthigh, x_axis, rad(-40), rad(300))
	Turn(lthigh, x_axis, rad(-25), rad(300))
	Turn(rshin, x_axis, rad(70), rad(400))
	Turn(lshin, x_axis, rad(60), rad(400))
	Turn(aim, x_axis, rad(60), rad(200))
	Turn(base, x_axis, rad(-85), rad(220))
	Move(base, y_axis, -1, 4)
	WaitForTurn(base, x_axis)
	Sleep(600)
	return 1
end
