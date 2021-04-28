import configparser


def check_config(name, settings):
    config = configparser.ConfigParser()
    config.read('settings.ini')
    settings = dict
    # checking for existing config
    if config.has_section(name):
        settings = dict(config.items(name))
    else:
        # writing default config, incase none has been found
        for key, data in settings.items():
            config['TEST']["{}".format(key)] = str(data)
        try:
            with open('settings.ini', 'a+') as configfile:
                config.write(configfile)
        except Exception as e:
            print('```error writing config: ' + str(e) + ' ```')
    return config, settings
