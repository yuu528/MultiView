import configparser

class Langs():
    def __init__(self, lang='en'):
        self.set_lang(lang)

    def set_lang(self, lang):
        self.lang_conf = configparser.ConfigParser()
        self.lang_conf.read('./lang/' + lang + '.ini', encoding='utf-8')

    def get(self, key):
        return self.lang_conf.get('LANGS', key, key)

    def get_all(self):
        return self.lang_conf['LANGS']
