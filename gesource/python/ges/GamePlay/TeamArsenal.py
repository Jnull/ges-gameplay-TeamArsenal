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
import GEUtil, GEMPGameRules as GERules, GEGlobal as Glb, GEPlayer, GEWeapon

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

        self.TEAM_SCORES = {
            Glb.TEAM_JANUS: {
                'name': "JANUS",
                'Levels': 0,
                'Kills': 0
            },
            Glb.TEAM_MI6: {
                'name': "MI6",
                'Levels': 0,
                'Kills': 0
            }
        }

    def GetPrintName(self):
        return "Team Arsenal"

    def GetScenarioHelp(self, help_obj):
        help_obj.SetDescription("At the start of the round, every team will be given a level 1 weapon. In order to level up towards the next weapon in the arsenal, your team score kills. \n\nSlapper kills will steal an entire level from the victim, and give the killer armor. \n\nThe first team to finish with the final weapon wins the round.")

    def GetGameDescription(self):
        return "Team Arsenal"

    def GetTeamPlay(self):
        return Glb.TEAMPLAY_ALWAYS

    def OnLoadGamePlay(self):
        GEUtil.PrecacheSound("GEGamePlay.Token_Drop_Enemy")  # Used for final weapon.
        GEUtil.PrecacheSound("GEGamePlay.Level_Up")  # Plays when level is gained
        GEUtil.PrecacheSound("GEGamePlay.Level_Down")  # Plays when level is lost

        self.CreateCVar("ar_lowestlevel", "1",
                        "Give new players the lowest active player's level. (Use 0 to start new players at level 1)")
        self.CreateCVar("ar_warmuptime", "15", "The warmup time in seconds. (Use 0 to disable)")
        self.CreateCVar("ar_killsperlevel", "1", "How many kills is required to level up to the next weapon.")
        self.CreateCVar("ar_slapsperplayer", "1", "How many slapper kill steals per player allowed. (Use 0 to disable)")

        # Make sure we don't start out in wait time or have a warmup if we changed gameplay mid-match
        if GERules.GetNumActivePlayers() >= 2:
            self.WaitingForPlayers = False
            self.warmupTimer.StartWarmup(0)

        GERules.EnableSuperfluousAreas()
        GERules.EnableInfiniteAmmo()
        GERules.SetAllowTeamSpawns(True)
        GERules.SetSpawnInvulnTime(1, False)

    def OnUnloadGamePlay(self):
        super(TeamArsenal, self).OnUnloadGamePlay()
        self.warmupTimer = None
        self.pltracker = None

    def OnCVarChanged(self, name, oldvalue, newvalue):
        if name == "ar_slapsperplayer":
            self.ar_slapsperplayer = int(newvalue)
        elif name == "ar_warmuptime":
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
        self.weaponList = []  # Clear our weapon list
        # Store all the current weaponset's weapons in a list for easy access.
        for i in range(0, 8):
            self.weaponList.append(GEWeapon.WeaponClassname(GERules.GetWeaponInSlot(i)))

        # Reset all player's statistics
        self.pltracker.SetValueAll(TR_SLAPPERKILLS, 0)

        #Track team levels and kills
        self.TEAM_SCORES = {
            Glb.TEAM_JANUS: {
                'name': "JANUS",
                'Levels': 0,
                'Kills': 0
            },
            Glb.TEAM_MI6: {
                'name': "MI6",
                'Levels': 0,
                'Kills': 0
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
        if not self.WaitingForPlayers and not self.warmupTimer.IsInWarmup():
            if player.IsInitialSpawn():
                GEUtil.PopupMessage(player, "Team Arsenal", "Your entire team is given a new \n weapon per team kills until the last weapon to win!")  # GES_GPH_AR_GOAL
            self.ar_PrintCurKills(player)
            self.ar_GivePlayerWeapons(player)
        elif(GERules.GetNumInRoundPlayers() == 1):
            #if in warmup, then roundbegin hasn't started, we need to set the team lvls
            GERules.GetTeam(Glb.TEAM_MI6).SetRoundScore(1)
            GERules.GetTeam(Glb.TEAM_JANUS).SetRoundScore(1)

    def OnPlayerKilled(self, victim, killer, weapon):
        if self.WaitingForPlayers or self.warmupTimer.IsInWarmup() or GERules.IsIntermission() or not victim:
            return
        vL = self.TEAM_SCORES[victim.GetTeamNumber()]['Levels']
        # Convert projectile entity names to their corresponding weapon
        name = weapon.GetClassname().lower()
        if name.startswith("npc_"):
            if name == "npc_grenade":
                name = "weapon_grenade"
            elif name == "npc_rocket":
                name = "weapon_rocket_launcher"
            elif name == "npc_shell":
                name = "weapon_grenade_launcher"
            elif name == "npc_mine_remote":
                name = "weapon_remotemine"
            elif name == "npc_mine_timed":
                name = "weapon_timedmine"
            elif name == "npc_mine_proximity":
                name = "weapon_proximitymine"

        if not killer or victim == killer:  # World kill or suicide
            self.ar_IncrementKills(victim, -1)
        else:
            # Normal kill
            if name == "weapon_slappers" or name == "player":  # Slappers or killbind.
                if vL > 0: #Since this is a slap or a suicude, then take a level if the Victims team level is greater than zero
                    if (self.ar_slapsperplayer == 0):  # if slaps per player then
                        self.ar_IncrementLevel(victim, -1)
                        self.ar_IncrementLevel(killer, 1)  # Jump forward an entire level, keeping our kill count.
                        GEUtil.EmitGameplayEvent("ar_levelsteal", str(killer.GetUserID()), str(victim.GetUserID()), "", "", True)  # Acheivement event
                        msg = _("#GES_GP_GUNGAME_SLAPPED", "^y" + victim.GetCleanPlayerName() + "^l on Team ^y" + str(self.TEAM_SCORES[victim.GetTeamNumber()]['name']) + "^l", killer.GetCleanPlayerName())
                        GEUtil.PostDeathMessage(msg)
                    elif (self.ar_slapsperplayer != 0 and self.pltracker[killer][TR_SLAPPERKILLS] < self.ar_slapsperplayer):  # if slaps per player is enabled make sure they are below ar_slapsperplayer
                        self.ar_IncrementLevel(victim, -1)
                        self.ar_IncrementLevel(killer, 1)  # Jump forward an entire level, keeping our kill count.
                        self.pltracker[killer][TR_SLAPPERKILLS] = self.pltracker[killer][TR_SLAPPERKILLS] + 1
                        GEUtil.EmitGameplayEvent("ar_levelsteal", str(killer.GetUserID()), str(victim.GetUserID()), "", "", True)  # Acheivement event
                        msg = _("#GES_GP_GUNGAME_SLAPPED", "^y" + victim.GetCleanPlayerName() + "^l on Team ^y" + str(self.TEAM_SCORES[victim.GetTeamNumber()]['name']) + "^l", killer.GetCleanPlayerName())
                        GEUtil.PostDeathMessage(msg)
                        if (self.pltracker[killer][TR_SLAPPERKILLS] == self.ar_slapsperplayer):
                            msg = _("^rYou cannot steal anymore levels!")
                            GEUtil.HudMessage(killer, msg, -1, 0.71, GEUtil.Color(220, 220, 220, 255), 3.0, 2)
                    else:
                        self.ar_IncrementKills(killer, 1)
                        msg = _("#GES_GP_GUNGAME_SLAPPED_NOLOSS", killer.GetCleanPlayerName())
                        GEUtil.PostDeathMessage(msg)
                else:
                    msg = _("#GES_GP_GUNGAME_SLAPPED_NOLOSS", killer.GetCleanPlayerName())
                    GEUtil.PostDeathMessage(msg)
                    self.ar_IncrementKills(killer, 1)  # We can't steal a whole level but we can at least get a kill.
                killer.SetArmor(int(Glb.GE_MAX_ARMOR))
            elif maxLevel == self.ar_GetLevel(killer):
                self.ar_IncrementKills(killer, 1)
            else:
                self.ar_IncrementKills(killer, 1)
        victim.StripAllWeapons()  # This prevents the victim from dropping weapons, which might confuse players since there are no pickups.

    # Advance the given player's level kills by the given amount.
    def ar_IncrementKills(self, player, amt):
        if(amt > 0 or amt < 0 and player.GetScore() > 0):
            self.ar_SetKills(player, self.TEAM_SCORES[player.GetTeamNumber()]['Kills'] + amt)
        player.SetScore(player.GetScore() + amt)

    # Advance the given player's level by the given amount.
    def ar_IncrementLevel(self, player, amt):
        if (self.TEAM_SCORES[player.GetTeamNumber()]['Levels'] + amt > 0):  # Make sure there's enough levels to take off
            self.ar_SetLevel(player, self.TEAM_SCORES[player.GetTeamNumber()]['Levels'] + amt)
        else:
            self.ar_SetKills(player, 0)  # If we can't take off a level we'll just take all of their kills.
            self.ar_SetLevel(player, 0)  # and set them to the lowest level, just in case someone changed the design of the mode and expected to take off 2 or more.

    def ar_SetKills(self, player, kills):
        if not player:
            return
        if (kills >= 1 + GERules.GetNumInRoundTeamPlayers(player.GetTeamNumber()) // 2):
            self.ar_IncrementLevel(player, 1)
            self.TEAM_SCORES[player.GetTeamNumber()]['Kills'] = 0
        elif (kills < 0):
            self.ar_IncrementLevel(player, -1)
            self.TEAM_SCORES[player.GetTeamNumber()]['Kills'] = 1 + GERules.GetNumInRoundTeamPlayers(player.GetTeamNumber()) // 2 - 1
        else:
            self.TEAM_SCORES[player.GetTeamNumber()]['Kills'] = kills
            for teamplayers in GetPlayers():
                if (teamplayers.GetTeamNumber() == player.GetTeamNumber()):
                    self.ar_PrintCurKills(teamplayers)

    # Set the given player's level to the given amount and give them their weapon.
    def ar_SetLevel(self, player, lvl):
        if not player:
            return

        oldlvl = (self.TEAM_SCORES[player.GetTeamNumber()]['Levels'])
        self.TEAM_SCORES[player.GetTeamNumber()]['Levels'] = lvl
        GERules.GetTeam(player.GetTeamNumber()).SetRoundScore(lvl + 1)  # Correcting for the fact that "self.TEAM_SCORES[player.GetTeamNumber()]['Levels']" starts at 0 in the code, 2 is 1, 3 is 2, etc.
        GEUtil.EmitGameplayEvent("ar_levelchange", str(player.GetUserID()), str(lvl))
        if lvl != oldlvl and lvl <= maxLevel:
            if self.ar_GetLevel(player) == maxLevel:  # Final level gets a special sound and announces to everyone.
                msg = _("#GES_GP_AR_FINALWEAPON", "^y" + player.GetCleanPlayerName() + "^l - Team ^y" + str(self.TEAM_SCORES[player.GetTeamNumber()]['name']))
                GEUtil.PostDeathMessage(msg)
                for allplayers in GetPlayers():
                    GEUtil.PlaySoundTo(allplayers, "GEGamePlay.Token_Grab_Enemy")
                    if (allplayers.GetTeamNumber() == OppositeTeam(player.GetTeamNumber())):
                        if(self.pltracker[allplayers][TR_SLAPPERKILLS] > 0):
                            self.pltracker[allplayers][TR_SLAPPERKILLS] = 0  # Reset all player slaps when a team is on last level
                            msg = _("^gYour slap kills have been reset! \n ^yThe other team is on the finale level!!")
                            GEUtil.HudMessage(allplayers, msg, -1, 0.71, GEUtil.Color(220, 220, 220, 255), 3.0, 2)
                        else:
                            msg = _("^yThe other team is on the finale level!!")
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
            #for allplayers in GetPlayers():  #i don't think this is necessary
                #GEUtil.EmitGameplayEvent("ar_completedarsenal", str(allplayers.GetUserID()), "", "", "", True)  # Used for acheivements so we have to send to clients
            GERules.EndRound()

    # Advance the given player's level kills by the given amount.
    def OnThink(self):
        # Check to see if we can get out of warmup
        if self.WaitingForPlayers and GERules.GetNumActivePlayers() > 1:
            self.WaitingForPlayers = False
            if not self.warmupTimer.HadWarmup():
                self.warmupTimer.StartWarmup(int(GEUtil.GetCVarValue("ar_warmuptime")), True)
            else:
                GERules.EndRound(False)

    def CanPlayerHaveItem(self, player, item):
        if (not player or player.GetTeamNumber() == Glb.TEAM_SPECTATOR or player.GetTeamNumber() == Glb.TEAM_NONE):
            return

        weapon = GEWeapon.ToGEWeapon(item)
        if weapon:
            name = weapon.GetClassname().lower()
            tL = int(self.TEAM_SCORES[player.GetTeamNumber()]['Levels'])
            if name == "weapon_slappers":
                return True
            if len(self.weaponList) < tL:
                return True
            if len(self.weaponList) == tL:
                return name == "weapon_knife"
            if name == self.weaponList[tL]:
                return True
            return False

    def CanMatchEnd(self):
        if GERules.IsIntermission() or GERules.GetNumActivePlayers() < 2:  # We just finished a round or it's not possible to get kills.
            return True
        else:
            return False

    # /////////////////////////// Utility Functions ///////////////////////////
    # Give player their level specific weapon and the slappers
    def ar_GivePlayerWeapons(self, player):
        if (not player or player.IsDead() or len(self.weaponList) < 7):
            return
        player.StripAllWeapons()
        player.GiveNamedWeapon("weapon_slappers", 0)  # We only ever have slappers and the weapon of our level
        lvl = int(self.TEAM_SCORES[player.GetTeamNumber()]['Levels'])
        if maxLevel > lvl:
            weap = self.weaponList[lvl]
        else:
            weap = "weapon_knife"  # Last level is always the knife.
        if weap != "weapon_slappers":
            player.GiveNamedWeapon(weap, 800)  # We use infinite ammo so who cares about exact ammo amounts
        player.WeaponSwitch(weap)

    # Present a HUD message with the player's current level
    def ar_PrintCurKills(self, player):
        if not player:
            return
        msg = _("#GES_GP_GUNGAME_KILLS", str(1 + GERules.GetNumInRoundTeamPlayers(player.GetTeamNumber()) // 2 - int(self.TEAM_SCORES[player.GetTeamNumber()]['Kills'])))  # We didn't increment a level which would have caused a level advancement message.
        GEUtil.HudMessage(player, msg, -1, 0.71, GEUtil.Color(220, 220, 220, 255), 1.5, 2)  # So give a killcount message instead.

    # Present a HUD message with the player's current level
    def ar_PrintCurLevel(self, player):
        if not player:
            return
        lvl = int(self.TEAM_SCORES[player.GetTeamNumber()]['Levels'])
        if lvl < maxLevel:
            name = GEWeapon.WeaponPrintName(self.weaponList[lvl])
        else:
            name = "Hunting Knife"
        msg = _("#GES_GP_GUNGAME_LEVEL", str(lvl + 1), name)
        GEUtil.HudMessage(player, msg, -1, 0.71, GEUtil.Color(220, 220, 220, 255), 3.0, 2)

    # Returns the given player's level
    def ar_GetLevel(self, player):
        if not player:
            return -1
        return self.TEAM_SCORES[player.GetTeamNumber()]['Levels']