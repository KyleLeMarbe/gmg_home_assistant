# Green Mountain Grill for Home Assistant

## **WARNING** This compoment is still in development. Use with caution!  

## Installation

Install via HACS 

<ul>
    <li>click 3 dots in top right</li>
    <li>Custom Repositories</li>
    <li>add this github URI as integration</li>
    <li>click add</li>
    </br>
    <li>click Explore & download repo bottom right</li>
    <li>Search & select Green Mountain Grill</li>
    <li>Click install</li>
</ul>

Add below to configuration.yaml in home assistant

```yaml
    #use the gmg platform with no other options to auto detect grill
    climate:
        - platform: gmg
```

```yaml
    #hard coded configuration will bypass auto detection
    climate:
        - platform: gmg
          host: x.x.x.x      #IP address of grill.  Recommend setting the grill to static IP on router
          grill_name: xxxxx  #Recommend using the grill serial number here GMGxxxxxxxx

```

## Requirements 

<ul>
    <li>UDP port 8080 open between home assistant & GMG (if on the same network, this should be open automatically)</li>
    <li>Auto discovery will discover multiple GMG devices if on same network as home assistant</li>
    <li>Your grills must be on and connected to wifi when restarting HomeAssistant when in Auto Discovery mode.  This will initialize your grills and add entities.</li>
</ul>

## TODO 

<ul>
    <li>Sensors for
        <ul>
            <li>food probes (temperature monitor.. set temperature etc.) - in development.. Set them up as climate as you can set temp for them 
                <ul>
                    <li>Need to better detect when probes are unplugged</li>
                </ul>
            </li>
            <li>Warning states</li>
            <li>Fire States</li>
        </ul>
    </li>
    <li>Test cold smoke mode</li>
    <li>Change Home assistant to use config flow for easier set up</li>
</ul>

## Test list

<ul>
    <li>Power on - successful</li>
    <li>Power off - successful</li>
    <li>Set temp - successful </br><b>Notes:</b> as recommended in GMG manual you shouldn't change temp until it reaches 150 F so I put in check to only change temp once that has been reached</li> 
    <li>Probes - successful</li>
</ul>
