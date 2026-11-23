-- Infantry don't explode: they fall over (see scripts/Units/people_soldier.lua).
return {
	people_death = {
		areaofeffect = 0,
		craterboost = 0,
		cratermult = 0,
		edgeeffectiveness = 0,
		explosiongenerator = "custom:blank",
		impulsefactor = 0,
		name = "Infantry death",
		soundhit = "",
		damage = {
			default = 0,
		},
	},
}
