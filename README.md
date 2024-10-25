# Warframe Stats
<img alt="warframe Logo" width=250 src="https://www-static.warframe.com/images/warframe/lotus-icon.svg">

[![GitHub Release](https://img.shields.io/github/release/mahss-io/warframe-stats.svg?style=for-the-badge)](https://github.com/mahss-io/warframe-stats/releases)
[![GitHub Release Date](https://img.shields.io/github/release-date/mahss-io/warframe-stats?label=Last%20Release&style=for-the-badge)](#warframe-stats)
[![GitHub Commit Activity](https://img.shields.io/github/commit-activity/y/mahss-io/warframe-stats.svg?style=for-the-badge)](https://github.com/mahss-io/warframe-stats/commits/master)
[![GitHub last commit](https://img.shields.io/github/last-commit/mahss-io/warframe-stats?style=for-the-badge)](#warframe-stats)
[![License](https://img.shields.io/github/license/mahss-io/warframe-stats?color=blue&style=for-the-badge)](LICENSE)<br/>
[![HACS](https://img.shields.io/badge/HACS-Default-blue.svg?style=for-the-badge)](https://github.com/hacs/integration)


_Component to pull data from and create sensors for the game Warframe._

#### Warframe Stats does not require but I arbitrarily choose to have it support v2024.10.0 and above. Be sure to upgrade. :D

## Installation
### HACS *(recommended)*
1. Ensure that [HACS](https://hacs.xyz/) is installed
1. Follow the steps provided by [HACS](https://hacs.xyz/docs/faq/custom_repositories/) for adding a `Custom Repositories`<br/>
  a. For the `Repository`, enter `mahss-io/warframe-stats`<br/>
  b. For the `Type`, enter `Integration`
1. [Click Here](https://my.home-assistant.io/redirect/hacs_repository/?owner=mahss-io&repository=warframe-stats) to directly open `warframe-stats` in HACS once its been added as a cutsom repository **or**<br/>
  a. Navigate to HACS<br/>
  b. Click `+ Explore & Download Repositories`<br/>
  c. Find the `Warframe Stats` integration <br/>
1. Click `Download`
1. Restart Home Assistant
1. See [Configuration](#configuration) below

### Manual
_You probably <u>do not</u> want to do this! Use the HACS method above unless you know what you are doing and have a good reason as to why you are installing manually_

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`)
1. If you do not have a `custom_components` directory there, you need to create it
1. In the `custom_components` directory create a new folder called `warframe`
1. Download _all_ the files from the `custom_components/warframe/` directory in this repository
1. Place the files you downloaded in the new directory you created
1. Restart Home Assistant
1. See [Configuration](#configuration) below

The file structure should look something like this. (I included the `configuration.yaml` file for reference)
```
/config/custom_components/configuration.yaml
/config/custom_components/warframe/__init__.py
/config/custom_components/warframe/config_flow.py
/config/custom_components/warframe/const.py
/config/custom_components/warframe/manifest.json
/config/custom_components/warframe/sensor.py
/config/custom_components/warframe/strings.json
/config/custom_components/warframe/translations
/config/custom_components/warframe/translations/en.json
```

## Configuration
The current configuration that is available is prompted when setting up this integration and can be reconfigured by selecting the integration going though the `Reconfigure` workflow (which is the same as the initial configuration workflow).

The current configuration options are:
* Warframes world state info - This is configured by a single `boolean` checkbox and will pull all the following stats.
  * Alerts
    * `state` - The number of current alerts.
    * `attributes` - The `node`,`reward`, and `missionType` of the missions associated with the alert.
  * Archon Hunt
    * `state` - The name of the current Archon
    * `attributes` - A list of missions with the following keys; `node`, `missionType`
  * World Cycles - This creates a separate sensor for the following worlds; Earth, Cetus, Orb Vallis, Cambion Drift, Zariman, Duviri.
    * `state` - The current state of the world. Examples (`day`,`night`,`warm`,`fass`).
    * `attributes` - If rewards are associated with the world (ie only bounties atm), they will be stored in the sensors attributes.
  * Fomorians and Razorbacks
    * `state` - `None` if no relay events are going on, else the name of the current event happening.
    * `attributes` - the % until the event occurs for each `fomorian` and `razorback` as the keys.
  * Events
    * `state` - The number of current events.
    * `attributes` - A list of events under the `events` key that include the `name` and `ends` time of the event.
  * Fissures - 3 versions of this sensor are created. One for regular Void Fissure missions, one for Steel Path missions, and one of Void Storms (Railjack) Void Fissure missions.
    * `state` - The number of current fissures missions of the given type.
    * `attributes` - A list of fissures under the `fissures` key containing the following keys for each fissures; `node`, `missionType`, `enemy`, `tier`.
  * Invasions
    * `state` - The number of current invasion missions currently available.
    * `attributes` - A list of missions under the `Invasions` key containing the following key for each missions; `node`, `rewardType` (which contains a list), `enemy`.
  * Sorties
    * `state` - A text sensor which is the 3 missions that make up the sorties concatenated by `-`.
    * `attributes` - A list of missions with the following keys; `node`, `missionType`, `modifier`.
  * Steel Path Honors
    * `state` - The current, weekly rotating, offering provided by Teshin.
  * Void Trader
    * `state` - Is either `Inactive` or `Active`
    * `attributes` - Contains a list of items under the `inventory` key.
  * Varzia
    * `state` - The current number of Primed Resurgence items provided by Varzia.
    * `attributes` - A list under the `items` key containing the following keys `name`, `aya`, `regal_aya`. Theses names are not translated/some of the names are not straight forwards on what they are.
* Specific Player Info - Can provide any number of usernames to pull info for.
  * Total Abilities Used
    * `state` - The total amount of abilities used. This does include other weird things like tenno abilities and pretty much special action bound to the same button as abilities.
    * `attributes` - A list under the `abilities` key with the following sub attributes; `name`, `used`.
  * Total Enemies Killed
    * `state` - The total amount of enemies killed.
    * `attributes` - A list under the `enemies killed` key with the following sub attributes; `name`, `killed`.
  * Most Scans Entity
    * `state` - The entity with the most scans. This includes enemies, plants, and objects.
    * `attributes` - A list under the `items scanned` key with the following sub attributes; `name`, `scans`. Some of the names are better _translated_
  * Deaths
    * `state` - I believe this is the total times the player has been downed.
    * `attributes` - A list under the `player_kills` key with the following sub attributes; `name`, `deaths`. Apparently the game keeps track of which enemies down the player, and theses are those stats.
  * Most Used <of_type> - This creates a sensor for the following types; `warframe`, `primary`, `secondary`, `melee`, `companion`, `archwing`, `arch-gun`, `arch-melee`.
    * `state` - The name of the most used item of the given type
    * `attributes` - A list under the type listed above with the following sub attributes; `uniqueName`, `xp`, `equiptime`, `assists`, `kills`, `fired`, `name`.
  * Total Lifetime Credits
    * `state` - The total amount of credits gained over the lifetime of the users account
    * `attributes` - A single value with the key, `credits per hour`, is the number of credits gain per hour.
  * Mastery Rank
    * `state` - A text sensor with the master rank of the player.
  * Time Played
    * `state` - The time played in hours. This is only the time spent in missions.
    * `attributes` - Converts the time played to seconds, minutes, hours, days and months.
  * Star Chart Completion
    * `state` - A value between 0 and 1 that is a percentage of total star chart completion
    * `attributes` - Two dicts under the `steel path` and `regular` key with the following sub attributes under the `node` key; `value`, `systemName`, `highScore`.

## How Warframe Stats Polls the API
I tired make it relatively efficient on how many API call the integration makes. For the world state info I am using the websocket, and I have never used a websocket before so could be better written.

* Static Data - Only used in the creation of a lookup table at the moment, which is updated on integration loading, and updated every week or if the Last Updated sensor value has changed.
* World State Data - This connects to a websocket and seeming get new data about every 30ish seconds.
* Player Statistic - The data is pulled very hour as it seems like the API does not update them that often either.

## TODO
* Fix Invasions not being a number statistic
* Rewrite Star Chart Completion attributes to align with other attributes this integration provides.
* For the Abilities Used, Deaths, and Enemies Killed, sensors store the 'Most' value in the attributes
* Fix unknown username when running through setup.
* Add an options config flow.
* Static Data sensors

## Notes
* For pulling user statistic, I think it breaks if the username is not able to be found and am not sure how it reacts to cross-platform usernames.
* To enable debug logging for this component, add the following to your `configuration.yaml` file
```yaml
logger:
  default: warning
  logs:
    custom_components.warframe: debug
```
