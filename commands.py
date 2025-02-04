import wikipediaapi
import nextcord


class Voice:
    def __init__(self, admin: nextcord.Member):
        self.admin: nextcord.Member = admin
        self.banned = set()


def find_user(dict_v: dict[int, Voice], member: nextcord.Member):
    for x in dict_v:
        if dict_v[x].admin.id == member:
            return x
    return None


def wiki_search(text):

    # установка языка (в данном случае используется язык, на котором говорит ассистент)
    wiki = wikipediaapi.Wikipedia('MyProjectName (merlin@example.com)', 'ru')

    # поиск страницы по запросу, чтение summary, открытие ссылки на страницу для получения подробной информации
    wiki_page = wiki.page(text)
    try:
        if wiki_page.exists():

            # чтение ассистентом первых двух предложений summary со страницы Wikipedia
            # (могут быть проблемы с мультиязычностью)
            wiki_answer = wiki_page.summary
            wiki_answer_good = wiki_answer[:wiki_answer.find(
                " (")] + wiki_answer[wiki_answer.find(") ") + 1:]
            answer = wiki_answer_good.split("\n")[0]

            return answer
        else:
            return 'Извините, мне не удалось найти это в Википедии'

    # поскольку все ошибки предсказать сложно, то будет произведен отлов с последующим выводом без остановки программы
    except:
        return 'Что-то пошло не так, попробуйте позже пожалуйста'
