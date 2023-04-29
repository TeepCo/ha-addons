# Home Assistant Add-on: Cumulus

[Cumulus add-on](github-link) connect your Home Assistant Instance via a secure tunnel to a domain or subdomain
at TeepCo Cumulus Cloud server. Doing that, you can expose your Home Assistant to the Internet without opening ports in your router.

### Prerequisites

- domain name (e.g. example.com) and account on TeepCo Cumulus Cloud
- created and initialized client instance on cloud server

## Installation

The installation of this add-on is pretty straightforward and not different in
comparison to installing any other Home Assistant add-on.

1. Click the Home Assistant My button below to open the add-on on your Home
   Assistant instance.

   [![Open this add-on in your Home Assistant instance.][addon-badge]][addon]

2. Click the "Install" button to install the add-on.
3. Configure add-on required settings (`server_url`, `client_id` and `client_secret`)
4. Start the "Cumulus" add-on.
5. Check the logs of the "Cumulus" to see if everything went well.
6. Change Home Assistant `http` configuration in **configuration.yaml** file
   ```yaml
   http:
      use_x_forwarded_for: true
      trusted_proxies:
         - 172.30.33.0/24
   ```
7. Ready to connect via your domain.

## Configuration

**Note**: _Remember to restart the add-on when the configuration is changed_

Example add-on configuration:

```yaml
server_url: wss://cumulus.teepco.cz
client_id: ea7d85e5-c144-4d61-9b04-4cc965d13981
client_secret: oTSXzX18KnZZILMc/Q/Jnzff3l0qThlQj1jYP5l9EiY=
log_level: debug
```

**Note**: _This is just an example, don't copy and paste it! Create your own!_

### Option: `server_url`

The url for web-socket connection to cloud server. Check your cloud account to get this value.

### Option: `client_id`

The identifier for your client instance on cloud server.

### Option: `client_secret`

The connection secret for your client instance on cloud server.

### Option: `log_level`

The `log_level` option controls the level of log output by the addon and can be changed to be more or less verbose,
which might be useful when you are dealing with an unknown issue. Possible values are:

- `debug`: Shows detailed debug information.
- `info`: Normal interesting events.
- `warning`: Exceptional occurences that are not errors.
- `error`: Runtime errors that do not require immediate action.
- `fatal`: Something went terribly wrong. Add-on becomes unusable.

Please note that each level automatically includes log messages from a more severe level, e.g., `debug` also shows `info` messages. By default, the `log_level` is set to `info`, which is the recommended setting unless you are troubleshooting.

[github-link]: https://github.com/TeepCo/ha-addons/tree/main/cumulus
[addon-badge]: https://my.home-assistant.io/badges/supervisor_addon.svg
[addon]: https://my.home-assistant.io/redirect/supervisor_addon/?addon=3289e81a_cumulus&repository_url=https%3A%2F%2Fgithub.com%2Fteepco%2Fha-addons
