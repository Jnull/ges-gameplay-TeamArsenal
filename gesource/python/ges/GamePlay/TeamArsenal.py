################ Copyright 2005-2016 Team GoldenEye: Source #################
#
# This file is part of GoldenEye: Source's Python Library.
#
# GoldenEye: Source's Python Library is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the License,
# or(at your option) any later version.
#
# GoldenEye: Source's Python Library is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GoldenEye: Source's Python Library.
# If not, see <http://www.gnu.org/licenses/>.
#############################################################################
from . import GEScenario
from .Utils.GEWarmUp import GEWarmUp
from .Utils import OppositeTeam, _
from .Utils.GEPlayerTracker import GEPlayerTracker
from .Utils import GetPlayers, clamp, _
import GEUtil, GEMPGameRules as GERules, GEGlobal as Glb, GEPlayer, GEWeapon, random






# Team_Arsenal
# Coded by Troy and Killer Monkey
# and completely ruined by E-S
# /////////////////////////// Scenario Data ///////////////////////////

USING_API = Glb.API_VERSION_1_2_0
maxLevel = 8
TR_SLAPPERKILLS = "slapperkills"
TR_LEVEL = "level"  # Player's current level.
TR_LEVELKILLS = "levelkills"  # How many kills the player has earned this level.

class TeamArsenal(GEScenario):
    def __init__(self):
        GEScenario.__init__(self)

        self.WaitingForPlayers = True
        self.weaponList = []
        self.warmupTimer = GEWarmUp(self)
        self.pltracker = GEPlayerTracker(self)
        # CVar Holders

        #Track team levels and kills
        self.TEAM_SCORES = {
            Glb.TEAM_JANUS: {
                'name': "JANUS",
                'color': "^r",
                'Levels': 0,
                'Kills': 0,
                'chars': ['boris', 'guard', 'infantry', 'ourumov', 'jaws', 'samedi', 'mayday', 'oddjob'],
            },
            Glb.TEAM_MI6: {
                'name': "MI6",
                'color': "^i",
                'Levels': 0,
                'Kills': 0,
                'chars': ['bond', '006_mi6', 'female_scientist', 'mishkin', 'valentin'],
            }
        }

        self.TEAM_SCORES[Glb.TEAM_JANUS]['random_char'] = random.choice (self.TEAM_SCORES[Glb.TEAM_JANUS]['chars'])
        self.TEAM_SCORES[Glb.TEAM_MI6]['random_char'] = random.choice (self.TEAM_SCORES[Glb.TEAM_MI6]['chars'])

    def GetPrintName(self):
        return "Team Arsenal"

    def GetScenarioHelp(self, help_obj):
        help_obj.SetDescription("At the start of the round, every team will be given a level 1 weapon. In order to level up towards the next weapon in the arsenal, your team score kills. \n\nSlapper kills will steal an entire level from the victim, and give the killer armor. \n\nThe first team to finish with the final weapon wins the round.")
        help_obj.SetInfo("Tag your it", "http://wiki.geshl2.com/")
    def GetGameDescription(self):
        return "Team Arsenal"

    def GetTeamPlay(self):
        return Glb.TEAMPLAY_ALWAYS

    def OnLoadGamePlay(self):
        GEUtil.PrecacheSound("GEGamePlay.Token_Drop_Enemy")  # Used for final weapon.
        GEUtil.PrecacheSound("GEGamePlay.Level_Up")  # Plays when level is gained
        GEUtil.PrecacheSound("GEGamePlay.Level_Down")  # Plays when level is lost
        #GEUtil.PrecacheSound("GEPlayer.Slapper")  # Plays when someone gets slapped

        self.CreateCVar("ta_warmuptime", "15", "The warmup time in seconds. (Use 0 to disable)")
        self.CreateCVar("ta_randomspawns", "1", "Random spawns enabled. (Use 0 to disable, teamspawns will be used instead)")
        self.CreateCVar("ar_slapsperplayer", "1", "How many slapper kill steals per player allowed. (Use 0 to disable)")
        self.CreateCVar("ar_onecharperteam", "1", "Each team is assigned one character each. (Use 0 to disable)")

        # Make sure we don't start out in wait time or have a warmup if we changed gameplay mid-match
        if GERules.GetNumActivePlayers() >= 2:
            self.WaitingForPlayers = False
            self.warmupTimer.StartWarmup(0)

        GERules.EnableSuperfluousAreas()
        GERules.EnableInfiniteAmmo()

        if self.ta_randomspawns == 1:
            GERules.SetAllowTeamSpawns(False)  #kill the other team but also find your team
        else:
            GERules.SetAllowTeamSpawns(True)  #kill the other team but also find your team

        GERules.SetSpawnInvulnTime(2, True)

        #for when round hasn't begun, we need to set the team lvls when theres only 1 person
        GERules.GetTeam(Glb.TEAM_MI6).SetRoundScore(1)
        GERules.GetTeam(Glb.TEAM_JANUS).SetRoundScore(1)

    def OnUnloadGamePlay(self):
        super(TeamArsenal, self).OnUnloadGamePlay()
        self.warmupTimer = None
        self.pltracker = None
        self.TEAM_SCORES = None

    def OnCVarChanged(self, name, oldvalue, newvalue):
        if name == "ta_randomspawns":
            self.ta_randomspawns = int(newvalue)
        if name == "ta_slapsperplayer":
            self.ta_slapsperplayer = int(newvalue)
        if name == "ta_onecharperteam":
            self.ta_onecharperteam = int(newvalue)
        elif name == "ta_warmuptime":
            if self.warmupTimer.IsInWarmup():
                val = int(newvalue)
                self.warmupTimer.StartWarmup(val)
                if val <= 0:
                    GERules.EndRound(False)

    def OnRoundBegin(self):
        GERules.AllowRoundTimer(False)
        GERules.DisableWeaponSpawns()
        GERules.DisableAmmoSpawns()
        GERules.DisableArmorSpawns()

        if self.ta_randomspawns == 1:
            GERules.SetAllowTeamSpawns(False)  #kill the other team but also find your team
        else:
            GERules.SetAllowTeamSpawns(True)  #kill the other team but also find your team

        self.weaponList = []  # Clear our weapon list
        # Store all the current weaponset's weapons in a list for easy access.
        for i in range(0, 8):
            self.weaponList.append(GEWeapon.WeaponClassname(GERules.GetWeaponInSlot(i)))

        # Reset all player's statistics
        self.pltracker.SetValueAll(TR_SLAPPERKILLS, 0)

        #Track team levels and kills
        self.TEAM_SCORES = {
            Glb.TEAM_JANUS: {
                'name': "Janus",
                'color': "^r",
                'Levels': 0,
                'Kills': 0,
                'chars': ['boris', 'guard', 'infantry', 'ourumov', 'jaws', 'samedi', 'mayday', 'oddjob'],
                'random_char': random.choice (self.TEAM_SCORES[Glb.TEAM_JANUS]['chars'])
            },
            Glb.TEAM_MI6: {
                'name': "MI6",
                'color': "^i",
                'Levels': 0,
                'Kills': 0,
                'chars': ['bond', '006_mi6', 'female_scientist', 'mishkin', 'valentin'],
                'random_char': random.choice (self.TEAM_SCORES[Glb.TEAM_MI6]['chars'])
            }
        }

        # Reset both team scores and player kills and deaths
        GERules.ResetAllPlayersScores()
        GERules.GetTeam(Glb.TEAM_MI6).SetRoundScore(1)
        GERules.GetTeam(Glb.TEAM_JANUS).SetRoundScore(1)

        for player in GetPlayers():
            if (player.GetTeamNumber() != Glb.TEAM_SPECTATOR and player.GetTeamNumber() != Glb.TEAM_NONE):
                self.ar_PrintCurLevel(player)

    def OnPlayerConnect(self, player):
        self.pltracker[player][TR_SLAPPERKILLS] = 0

    def OnPlayerSpawn(self, player):
        #one character per team
        if player and player.GetTeamNumber() == Glb.TEAM_JANUS and not player.GetPlayerModel().lower() == self.TEAM_SCORES[Glb.TEAM_JANUS]['random_char'] and self.ta_onecharperteam == 1:
            player.SetPlayerModel(self.TEAM_SCORES[Glb.TEAM_JANUS]['random_char'], 0)
        if player and player.GetTeamNumber() == Glb.TEAM_MI6 and not player.GetPlayerModel().lower() == self.TEAM_SCORES[Glb.TEAM_MI6]['random_char'] and self.ta_onecharperteam == 1:
            player.SetPlayerModel(self.TEAM_SCORES[Glb.TEAM_MI6]['random_char'], 0)
        if not self.WaitingForPlayers and not self.warmupTimer.IsInWarmup():
            if player.IsInitialSpawn():
                GEUtil.PopupMessage(player, "Team Arsenal", "Your entire team is given a new \n weapon depending on your team level, which is determined by your team kills until the last weapon to win!")  # GES_GPH_AR_GOAL
            self.ar_PrintCurKills(player)
            self.ar_GivePlayerWeapons(player)

    def OnPlayerKilled(self, victim, killer, weapon):
        if self.WaitingForPlayers or self.warmupTimer.IsInWarmup() or GERules.IsIntermission() or not victim:
            return
        victim.StripAllWeapons()  # This prevents the victim from dropping weapons, which might confuse players since there are no pickups.
        vL = self.TEAM_SCORES[victim.GetTeamNumber()]['Levels']
        name = weapon.GetClassname().lower()
        if not killer or victim == killer:  # World kill or suicide
            self.ar_IncrementKills(victim, -1)
        else:
            if name == "weapon_slappers" or name == "player":  # Slappers kill
                if vL > 0: #Victims Team Level is greater than zero
                    if self.ta_slapsperplayer == 0 or self.ta_slapsperplayer != 0 and self.pltracker[killer][TR_SLAPPERKILLS] < self.ta_slapsperplayer:  # if slaps per player limit is 0: disabled (unlimited slaps) or less than slapsperplayer threshhold
                        self.pltracker[killer][TR_SLAPPERKILLS] = self.pltracker[killer][TR_SLAPPERKILLS] + 1 #increment slap per player
                        self.ar_IncrementLevel(victim, -1)
                        self.ar_IncrementLevel(killer, 1)  # Jump forward an entire level, keeping our kill count.
                        #GEUtil.EmitGameplayEvent("ar_levelsteal", str(killer.GetUserID()), str(victim.GetUserID()), "", "", True)  # Acheivement event
                        if self.pltracker[killer][TR_SLAPPERKILLS] == self.ta_slapsperplayer:
                            msg = _("^rYou cannot steal anymore levels!")
                            GEUtil.HudMessage(killer, msg, -1, 0.71, GEUtil.Color(220, 220, 220, 255), 3.0, 2)
                        msg = _(str(self.TEAM_SCORES[killer.GetTeamNumber()]['color']) + killer.GetCleanPlayerName() + "^l gained armor" + " and a level for Team " + str(self.TEAM_SCORES[killer.GetTeamNumber()]['color']) + str(self.TEAM_SCORES[killer.GetTeamNumber()]['name']) + "!" + "\n" + str(self.TEAM_SCORES[victim.GetTeamNumber()]['color']) + victim.GetCleanPlayerName() + " ^llost a level ^w- ^lTeam " + str(self.TEAM_SCORES[victim.GetTeamNumber()]['color']) + str(self.TEAM_SCORES[victim.GetTeamNumber()]['name']) + "!")
                        GEUtil.PostDeathMessage(msg)
                    else: #too many slapper steals increment player 1 kill only
                        self.ar_IncrementKills(killer, 1)
                        msg = _(str(self.TEAM_SCORES[killer.GetTeamNumber()]['color']) + killer.GetCleanPlayerName() + "^l gained armor!")
                        GEUtil.PostDeathMessage(msg)
                else: #if Victim Team Level is below 1, then just give player a team kill
                    msg = _(str(self.TEAM_SCORES[killer.GetTeamNumber()]['color']) + killer.GetCleanPlayerName() + "^l gained armor!")
                    GEUtil.PostDeathMessage(msg)
                    self.ar_IncrementKills(killer, 1)  # We can't steal a whole level but we can at least get a kill.
                killer.SetArmor(int(Glb.GE_MAX_ARMOR))
                killer.SetScore(killer.GetScore() + 1)
            else:
                self.ar_IncrementKills(killer, 1) # Normal kill

    # Advance the given player's level kills by the given amount.
    def ar_IncrementKills(self, player, amt):
        if(amt > 0 or amt < 0 and player.GetScore() > 0):
            self.ar_SetKills(player, int(self.TEAM_SCORES[player.GetTeamNumber()]['Kills']) + amt)
        player.SetScore(player.GetScore() + amt)

    # Advance the given player's level by the given amount.
    def ar_IncrementLevel(self, player, amt):
        if (int(self.TEAM_SCORES[player.GetTeamNumber()]['Levels']) + amt > 0):  # Make sure there's enough levels to take off
            self.ar_SetLevel(player, int(self.TEAM_SCORES[player.GetTeamNumber()]['Levels']) + amt)
        else:
            self.ar_SetKills(player, 0)  # If we can't take off a level we'll just take all of their kills.
            self.ar_SetLevel(player, 0)  # and set them to the lowest level, just in case someone changed the design of the mode and expected to take off 2 or more.

    def ar_SetKills(self, player, kills):
        ##if not player:
        ##    return
        if (kills >= 1 + GERules.GetNumInRoundTeamPlayers(player.GetTeamNumber()) // 2): #advance 1 level (Team have enough kills)
            self.ar_IncrementLevel(player, 1)
            self.TEAM_SCORES[player.GetTeamNumber()]['Kills'] = 0
        elif (kills < 0): #team kills are neg
            self.ar_IncrementLevel(player, -1)
            self.TEAM_SCORES[player.GetTeamNumber()]['Kills'] = 1 + GERules.GetNumInRoundTeamPlayers(player.GetTeamNumber()) // 2 - 1  #minus one kill from team for player dying
        else:
            self.TEAM_SCORES[player.GetTeamNumber()]['Kills'] = kills
            for teamplayers in GetPlayers():
                if (teamplayers.GetTeamNumber() == player.GetTeamNumber()):
                    self.ar_PrintCurKills(teamplayers)

    # Set the given player's level to the given amount and give them their weapon.
    def ar_SetLevel(self, player, lvl):
        ##if not player:
        ##    return

        oldlvl = (self.TEAM_SCORES[player.GetTeamNumber()]['Levels'])
        self.TEAM_SCORES[player.GetTeamNumber()]['Levels'] = lvl
        GERules.GetTeam(player.GetTeamNumber()).SetRoundScore(lvl + 1)  # Correcting for the fact that "self.TEAM_SCORES[player.GetTeamNumber()]['Levels']" starts at 0 in the code, 2 is 1, 3 is 2, etc.
        if lvl != oldlvl and lvl <= maxLevel:
            if self.ar_GetLevel(player) == maxLevel:  # Final level gets a special sound and announces to everyone.
                msg = _("#GES_GP_AR_FINALWEAPON", "^y" + player.GetCleanPlayerName() + "^l - Team ^y" + str(self.TEAM_SCORES[player.GetTeamNumber()]['name']))
                GEUtil.PostDeathMessage(msg)
                for allplayers in GetPlayers():
                    GEUtil.PlaySoundTo(allplayers, "GEGamePlay.Token_Grab_Enemy")
                    if (allplayers.GetTeamNumber() == OppositeTeam(player.GetTeamNumber())):
                        if(self.pltracker[allplayers][TR_SLAPPERKILLS] > 0 and self.ta_slapsperplayer != 0):
                            self.pltracker[allplayers][TR_SLAPPERKILLS] = 0  # Reset all player slaps when a team is on last level
                            msg = _("^hYour slap kills have been reset! \n ^yThe other team is on the final level^h!!")
                        else:
                            msg = _("^yThe other team is on the final level^h!!")
                        GEUtil.HudMessage(allplayers, msg, -1, 0.71, GEUtil.Color(220, 220, 220, 255), 3.0, 2)

            elif lvl > oldlvl:  # Gained a level
                for teamplayers in GetPlayers():
                    if (teamplayers.GetTeamNumber() == player.GetTeamNumber()):
                        GEUtil.PlaySoundTo(teamplayers, "GEGamePlay.Level_Up")
            else:  # Lost a level.
                for teamplayers in GetPlayers():
                    if (teamplayers.GetTeamNumber() == player.GetTeamNumber()):
                        GEUtil.PlaySoundTo(teamplayers, "GEGamePlay.Level_Down")

        # Give weapons and print level.
        if lvl <= maxLevel:  # give weapons if current lvl is under max level.
            for teamplayers in GetPlayers():
                if (teamplayers.GetTeamNumber() == player.GetTeamNumber()):
                    self.ar_PrintCurLevel(teamplayers)
                    self.ar_GivePlayerWeapons(teamplayers)
        elif not GERules.IsIntermission():  # In fact, if we are, we just won!
            GERules.EndRound()

    # Advance the given player's level kills by the given amount.
    def OnThink(self):
        if self.WaitingForPlayers and GERules.GetNumActivePlayers() > 1:  # More than 1 player? start warmup timer!
            self.WaitingForPlayers = False
            if self.warmupTimer.HadWarmup():
                pass
                #GERules.EndRound(False)  #do we really need this?
            else:
                self.warmupTimer.StartWarmup(int(GEUtil.GetCVarValue("ta_warmuptime")), True)

    def CanPlayerHaveItem(self, player, item):
        if (player.GetTeamNumber() == Glb.TEAM_SPECTATOR or player.GetTeamNumber() == Glb.TEAM_NONE):  ##not player or
            return

        weapon = GEWeapon.ToGEWeapon(item)
        if weapon:
            name = weapon.GetClassname().lower()
            tl = int(self.TEAM_SCORES[player.GetTeamNumber()]['Levels'])
            if len(self.weaponList) > tl:  #if cur lvl is less than knife: give slappers and lvl weapon only.
                return name == "weapon_slappers" or name == self.weaponList[tl]
            if len(self.weaponList) <= tl: #if cur lvl is knife or greater: give slappers and knife only.
                return name == "weapon_slappers" or name == "weapon_knife"
            return False

    def CanMatchEnd(self):
        if GERules.IsIntermission() or GERules.GetNumActivePlayers() < 2:  # End round if not enough players or Intermission().
            return True
        else:
            return False

    # Give player their level specific weapon and the slappers
    def ar_GivePlayerWeapons(self, player):
        if player.IsDead():  ##not player or
            return
        player.StripAllWeapons()
        lvl = int(self.TEAM_SCORES[player.GetTeamNumber()]['Levels'])
        player.GiveNamedWeapon("weapon_slappers", 0)  #always have slappers
        if maxLevel > lvl:
            weap = self.weaponList[lvl]
        else:
            weap = "weapon_knife"  # Last level is always the knife.
        if weap != "weapon_slappers":
            player.GiveNamedWeapon(weap, 800) #(weapon_name, ammo)
        player.WeaponSwitch(weap)

    # Present a HUD message with the player's current level
    def ar_PrintCurKills(self, player):
        msg = _("#GES_GP_GUNGAME_KILLS", str(1 + GERules.GetNumInRoundTeamPlayers(player.GetTeamNumber()) // 2 - int(self.TEAM_SCORES[player.GetTeamNumber()]['Kills'])))  # We didn't increment a level which would have caused a level advancement message.
        GEUtil.HudMessage(player, msg, -1, 0.71, GEUtil.Color(220, 220, 220, 255), 1.5, 2)

    # Present a HUD message with the player's current level
    def ar_PrintCurLevel(self, player):
        lvl = int(self.TEAM_SCORES[player.GetTeamNumber()]['Levels'])
        if lvl < maxLevel:
            name = GEWeapon.WeaponPrintName(self.weaponList[lvl])
        else:
            name = "Hunting Knife"
        msg = _("#GES_GP_GUNGAME_LEVEL", str(lvl + 1), name)
        GEUtil.HudMessage(player, msg, -1, 0.71, GEUtil.Color(220, 220, 220, 255), 3.0, 2)

    # Returns the given player's level
    def ar_GetLevel(self, player):
        return self.TEAM_SCORES[player.GetTeamNumber()]['Levels']
