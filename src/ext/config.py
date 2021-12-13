import configparser


def check_config(name, settings=None):
    config = configparser.ConfigParser()
    config.read('settings.ini', encoding="utf-16")
    # checking for existing config
    if config.has_section(name):
        settings = dict(config.items(name))
    else:
        # writing default config, incase none has been found
        config.add_section(name)
        for key, data in settings.items():
            config[name]["{}".format(key)] = str(data)
        try:
            with open('settings.ini', 'w+', encoding="utf-16") as configfile:
                config.write(configfile)
        except Exception as e:
            print('```error writing config: ' + str(e) + ' ```')
    return config, settings


def save_config(config):
    with open('settings.ini', 'w+', encoding="utf-16") as configfile:
        config.write(configfile)
        return True
