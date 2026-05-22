import os
import sys
import json
import random
import threading
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox, ttk

# Resolve base directories and import core guardian module
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
import guardian

# ==================== THEME & STYLE CONSTANTS (APPLE PREMIUM DARK MODE) ====================
BG_DARK = "#09090B"          # Pure deep charcoal/black (Midnight)
BG_CARD = "#121214"          # Sleek Space Black card background
BG_INNER = "#1C1C1E"         # Apple premium dark gray inner container
FG_LIGHT = "#F5F5F7"         # Apple primary white text
FG_SECONDARY = "#8E8E93"     # Apple secondary gray text
ACCENT_CYAN = "#0071E3"      # Apple royal signature blue (primary interactive accent)
ACCENT_GREEN = "#30D158"     # Apple vibrant system green (success/completed)
ACCENT_RED = "#FF453A"       # Apple vibrant system red (error/warning)
ACCENT_ORANGE = "#FF9F0A"    # Apple vibrant system orange (stats/countdowns)
ACCENT_PURPLE = "#BF5AF2"    # Apple vibrant system purple (special icons)
HOVER_COLOR = "#222225"      # Minimalist card hover background
BORDER_COLOR = "#2C2C2E"     # Thin clean outline divider

FONT_FAMILY = "Segoe UI" if os.name == "nt" else "Arial"

# ==================== PRE-DEFINED GRAMMAR CURRICULUM ====================
GRAMMAR_LESSONS = [
    {
        "id": "wa_particle",
        "title": "Lesson 1: Topic Marker (は - wa)",
        "desc": "The particle は (pronounced 'wa') is the topic marker. It establishes the main topic of your sentence, which is then described.",
        "concept": "Topic [Noun] + は + Description [Noun/Adjective] + です\nExample: 私は学生です (As for me, I am a student).",
        "examples": [
            {"ja": "私は学生です。", "romaji": "watashi wa gakusei desu.", "en": "I am a student.", "pron": "わたしはがくせいです。"},
            {"ja": "これは本です。", "romaji": "kore wa hon desu.", "en": "This is a book.", "pron": "これはほんです。"}
        ],
        "builder": {
            "english": "I am a student.",
            "correct_order": ["私", "は", "学生", "です"],
            "options": ["学生", "は", "に", "私", "です", "猫"]
        }
    },
    {
        "id": "ga_particle",
        "title": "Lesson 2: Subject Marker (が - ga)",
        "desc": "The particle が marks the specific subject that performs an action or exists. While は emphasizes the description, が emphasizes the subject itself.",
        "concept": "Subject [Noun] + が + います (living objects) / あります (inanimate objects)\nExample: 猫がいます (There is a cat).",
        "examples": [
            {"ja": "猫がいます。", "romaji": "neko ga imasu.", "en": "There is a cat.", "pron": "ねこがいます。"},
            {"ja": "水があります。", "romaji": "mizu ga arimasu.", "en": "There is water.", "pron": "みずがあります。"}
        ],
        "builder": {
            "english": "There is a cat.",
            "correct_order": ["猫", "が", "います"],
            "options": ["猫", "は", "が", "います", "あります", "犬"]
        }
    },
    {
        "id": "o_particle",
        "title": "Lesson 3: Direct Object (を - o)",
        "desc": "The particle を (pronounced 'o') marks the direct object of a transitive verb. It indicates what is being acted upon.",
        "concept": "Object [Noun] + を + Verb [Action]\nExample: 本を読みます (I read a book).",
        "examples": [
            {"ja": "本を読みます。", "romaji": "hon o yomimasu.", "en": "I read a book.", "pron": "ほんをよみます。"},
            {"ja": "水を飲みます。", "romaji": "mizu o nomimasu.", "en": "I drink water.", "pron": "みずをのみます。"}
        ],
        "builder": {
            "english": "I read a book.",
            "correct_order": ["本", "を", "読みます"],
            "options": ["本", "に", "を", "読みます", "飲みます", "水"]
        }
    },
    {
        "id": "ni_particle",
        "title": "Lesson 4: Direction/Time (に - ni)",
        "desc": "The particle に has multiple uses, but its most core are marking: 1) a specific point in time, and 2) the destination of motion verbs.",
        "concept": "Destination [Noun] + に + 行きます (go) / 来ます (come)\nExample: 日本に行きます (I go to Japan).",
        "examples": [
            {"ja": "日本に行きます。", "romaji": "nihon ni ikimasu.", "en": "I go to Japan.", "pron": "にほん に いきます。"},
            {"ja": "駅に行きます。", "romaji": "eki ni ikimasu.", "en": "I go to the station.", "pron": "えき に いきます。"}
        ],
        "builder": {
            "english": "I go to Japan.",
            "correct_order": ["日本", "に", "行きます"],
            "options": ["日本", "を", "に", "行きます", "来ます", "駅"]
        }
    },
    {
        "id": "polite_verbs",
        "title": "Lesson 5: Polite Conjugation (~ます)",
        "desc": "Verbs in Japanese end in a dictionary form (plain). To speak politely, we conjugate them into the '~masu' form for present, and '~mashita' for past.",
        "concept": "行く (iku / go) ➔ 行きます (ikimasu / polite present)\n行く ➔ 行きました (ikimashitai / polite past)\n行く ➔ 行きません (ikimasen / polite present negative)",
        "examples": [
            {"ja": "行きました。", "romaji": "ikimashia.", "en": "I went.", "pron": "いきました。"},
            {"ja": "食べません。", "romaji": "tabemasen.", "en": "I do not eat.", "pron": "たべません。"}
        ],
        "builder": {
            "english": "I went to the school (学校).",
            "correct_order": ["学校", "に", "行きました"],
            "options": ["学校", "に", "を", "行きます", "行きました", "日本"]
        }
    },
    {
        "id": "adjectives",
        "title": "Lesson 6: Adjectives (い vs な)",
        "desc": "Japanese adjectives fall into two classes: i-adjectives (end in 'i' natively) and na-adjectives (require 'na' to connect to nouns).",
        "concept": "i-adj: 新しい車 (atarashii kuruma / new car) ➔ Connects directly.\nna-adj: 有名な人 (yuumei na hito / famous person) ➔ Requires 'na'.",
        "examples": [
            {"ja": "新しい車です。", "romaji": "atarashii kuruma desu.", "en": "It is a new car.", "pron": "あたらしいくるまです。"},
            {"ja": "有名な人です。", "romaji": "yuumei na hito desu.", "en": "He/she is a famous person.", "pron": "ゆうめいなひとです。"}
        ],
        "builder": {
            "english": "It is a new car.",
            "correct_order": ["新しい", "車", "です"],
            "options": ["新しい", "車", "な", "有名", "です", "猫"]
        }
    }
]

# ==================== PRE-DEFINED JLPT KANJI DATABASE (N5 TO N1) ====================
JLPT_KANJI_DATABASE = {
    "N5": [
        {"kanji": "日", "meaning": "day, sun", "onyomi": "ニチ, ジツ", "kunyomi": "ひ, び", "stroke_count": 4, "example_ja": "日本にいきたいです。", "example_en": "I want to go to Japan.", "kanji_yomi": "ひ", "kanji_romaji": "hi", "example_yomi": "にほん に いきたい です。", "example_romaji": "nihon ni ikitai desu."},
        {"kanji": "本", "meaning": "book, origin", "onyomi": "ホン", "kunyomi": "もと", "stroke_count": 5, "example_ja": "これは私の本です。", "example_en": "This is my book.", "kanji_yomi": "ほん", "kanji_romaji": "hon", "example_yomi": "これ は わたし の ほん です。", "example_romaji": "kore wa watashi no hon desu."},
        {"kanji": "人", "meaning": "person", "onyomi": "ジン, ニン", "kunyomi": "ひと", "stroke_count": 2, "example_ja": "あの人は先生です。", "example_en": "That person is a teacher.", "kanji_yomi": "ひと", "kanji_romaji": "hito", "example_yomi": "あの ひと は せんせい です。", "example_romaji": "ano hito wa sensei desu."},
        {"kanji": "学", "meaning": "study, learn", "onyomi": "ガク", "kunyomi": "まな-ぶ", "stroke_count": 8, "example_ja": "日本語を学びます。", "example_en": "I learn Japanese.", "kanji_yomi": "まなぶ", "kanji_romaji": "manabu", "example_yomi": "にほんご を まなびます。", "example_romaji": "nihongo o manabimasu."},
        {"kanji": "校", "meaning": "school", "onyomi": "コウ", "kunyomi": "(none)", "stroke_count": 10, "example_ja": "学校に行きます。", "example_en": "I go to school.", "kanji_yomi": "こう", "kanji_romaji": "kou", "example_yomi": "がっこう に いきます。", "example_romaji": "gakkou ni ikimasu."}
    ],
    "N4": [
        {"kanji": "犬", "meaning": "dog", "onyomi": "ケン", "kunyomi": "いぬ", "stroke_count": 4, "example_ja": "黒い犬がいます。", "example_en": "There is a black dog.", "kanji_yomi": "いぬ", "kanji_romaji": "inu", "example_yomi": "くろい いぬ が います。", "example_romaji": "kuroi inu ga imasu."},
        {"kanji": "猫", "meaning": "cat", "onyomi": "ビョウ", "kunyomi": "ねこ", "stroke_count": 11, "example_ja": "猫が寝ています。", "example_en": "The cat is sleeping.", "kanji_yomi": "ねこ", "kanji_romaji": "neko", "example_yomi": "ねこ が ねています。", "example_romaji": "neko ga neteimasu."},
        {"kanji": "魚", "meaning": "fish", "onyomi": "ギョ", "kunyomi": "さかな", "stroke_count": 11, "example_ja": "魚が泳いでいます。", "example_en": "Fish is swimming.", "kanji_yomi": "さかな", "kanji_romaji": "sakana", "example_yomi": "さかな が およいで います。", "example_romaji": "sakana ga oyoide imasu."},
        {"kanji": "雨", "meaning": "rain", "onyomi": "ウ", "kunyomi": "あめ", "stroke_count": 8, "example_ja": "雨が降っています。", "example_en": "It is raining.", "kanji_yomi": "あめ", "kanji_romaji": "ame", "example_yomi": "あめ が ふっています。", "example_romaji": "ame ga futteimasu."},
        {"kanji": "空", "meaning": "sky, empty", "onyomi": "クウ", "kunyomi": "そら", "stroke_count": 8, "example_ja": "青い空がきれいです。", "example_en": "The blue sky is beautiful.", "kanji_yomi": "そら", "kanji_romaji": "sora", "example_yomi": "あおい そら が きれいです。", "example_romaji": "aoi sora ga kirei desu."}
    ],
    "N3": [
        {"kanji": "旅", "meaning": "travel, trip", "onyomi": "リョ", "kunyomi": "たび", "stroke_count": 10, "example_ja": "一人で旅をします。", "example_en": "I travel alone.", "kanji_yomi": "たび", "kanji_romaji": "tabi", "example_yomi": "ひとり で たび を します。", "example_romaji": "hitori de tabi o shimasu."},
        {"kanji": "界", "meaning": "world, boundary", "onyomi": "カイ", "kunyomi": "(none)", "stroke_count": 9, "example_ja": "世界は広いです。", "example_en": "The world is wide.", "kanji_yomi": "かい", "kanji_romaji": "kai", "example_yomi": "せかい は ひろいです。", "example_romaji": "sekai wa hiroi desu."},
        {"kanji": "変", "meaning": "change, strange", "onyomi": "ヘン", "kunyomi": "か-わる", "stroke_count": 9, "example_ja": "天気が変わりました。", "example_en": "The weather changed.", "kanji_yomi": "かわる", "kanji_romaji": "kawaru", "example_yomi": "てんき が かわりました。", "example_romaji": "tenki ga kawarimashita."},
        {"kanji": "選", "meaning": "choose, select", "onyomi": "セン", "kunyomi": "えら-ぶ", "stroke_count": 15, "example_ja": "好きなものを選んでください。", "example_en": "Please choose your favorite one.", "kanji_yomi": "えらぶ", "kanji_romaji": "erabu", "example_yomi": "すきな もの を えらんで ください。", "example_romaji": "sukina mono o erande kudasai."},
        {"kanji": "調", "meaning": "investigate, tone", "onyomi": "チョウ", "kunyomi": "しら-べる", "stroke_count": 15, "example_ja": "辞書で意味を調べます。", "example_en": "I look up the meaning in a dictionary.", "kanji_yomi": "しらべる", "kanji_romaji": "shiraberu", "example_yomi": "じしょ で いみ を しらべます。", "example_romaji": "jisho de imi o shirabemasu."}
    ],
    "N2": [
        {"kanji": "資", "meaning": "assets, resources", "onyomi": "シ", "kunyomi": "(none)", "stroke_count": 13, "example_ja": "地球の資源を守ります。", "example_en": "Protect earth's resources.", "kanji_yomi": "しげん", "kanji_romaji": "shigen", "example_yomi": "ちきゅう の しげん を まもります。", "example_romaji": "chikyuu no shigen o mamorimasu."},
        {"kanji": "製", "meaning": "manufacture", "onyomi": "セイ", "kunyomi": "(none)", "stroke_count": 14, "example_ja": "これは日本製です。", "example_en": "This is made in Japan.", "kanji_yomi": "せい", "kanji_romaji": "sei", "example_yomi": "これ は にほんせい です。", "example_romaji": "kore wa nihonsei desu."},
        {"kanji": "賞", "meaning": "prize, award", "onyomi": "ショウ", "kunyomi": "(none)", "stroke_count": 15, "example_ja": "彼はノーベル賞を受賞した。", "example_en": "He won the Nobel Prize.", "kanji_yomi": "しょう", "kanji_romaji": "shou", "example_yomi": "かれ は のーべるしょう を じゅしょう した。", "example_romaji": "kare wa nooberushou o jushou shita."},
        {"kanji": "優", "meaning": "excellent, gentle", "onyomi": "ユウ", "kunyomi": "やさ-しい", "stroke_count": 17, "example_ja": "彼は優しい人です。", "example_en": "He is a gentle person.", "kanji_yomi": "やさしい", "kanji_romaji": "yasashii", "example_yomi": "かれ は やさしい ひと です。", "example_romaji": "kare wa yasashii hito desu."},
        {"kanji": "防", "meaning": "prevent, defend", "onyomi": "ボウ", "kunyomi": "ふせ-ぐ", "stroke_count": 7, "example_ja": "病気を防ぎます。", "example_en": "Prevent illnesses.", "kanji_yomi": "ふせぐ", "kanji_romaji": "fusegu", "example_yomi": "びょうき を ふせぎます。", "example_romaji": "byouki o fusegimasu."}
    ],
    "N1": [
        {"kanji": "微", "meaning": "delicate, microscopic", "onyomi": "ビ", "kunyomi": "(none)", "stroke_count": 13, "example_ja": "微かな光が見えます。", "example_en": "I can see a faint light.", "kanji_yomi": "かすか", "kanji_romaji": "kasuka", "example_yomi": "かすかな ひかり が みえます。", "example_romaji": "kasukana hikari ga miemasu."},
        {"kanji": "妙", "meaning": "exquisite, strange", "onyomi": "ミョウ", "kunyomi": "(none)", "stroke_count": 7, "example_ja": "妙な音が聞こえます。", "example_en": "I hear a strange sound.", "kanji_yomi": "みょう", "kanji_romaji": "myou", "example_yomi": "みょうな おと が きこえます。", "example_romaji": "myouna oto ga kikoemasu."},
        {"kanji": "輝", "meaning": "sparkle, shine", "onyomi": "キ", "kunyomi": "かがや-く", "stroke_count": 15, "example_ja": "星が輝いています。", "example_en": "Stars are shining.", "kanji_yomi": "かがやく", "kanji_romaji": "kagayaku", "example_yomi": "ほし が かがやいて います。", "example_romaji": "hoshi ga kagayaiter imasu."},
        {"kanji": "驚", "meaning": "wonder, surprise", "onyomi": "キョウ", "kunyomi": "おどろ-く", "stroke_count": 22, "example_ja": "ニュースに驚きました。", "example_en": "I was surprised by the news.", "kanji_yomi": "おどろく", "kanji_romaji": "odoroku", "example_yomi": "にゅーす に おどろきました。", "example_romaji": "nyuusu ni odorokimashita."},
        {"kanji": "護", "meaning": "protect, defend", "onyomi": "ゴ", "kunyomi": "まも-る", "stroke_count": 20, "example_ja": "自然環境を保護します。", "example_en": "Protect the natural environment.", "kanji_yomi": "ほご", "kanji_romaji": "hogo", "example_yomi": "しぜん かんきょう を ほご します。", "example_romaji": "shizen kankyou o hogo shimasu."}
    ]
}

# ==================== PRE-DEFINED JLPT GRAMMAR CURRICULUM ====================
JLPT_GRAMMAR_LESSONS = {
    "N5": [
        GRAMMAR_LESSONS[0],
        GRAMMAR_LESSONS[1],
        GRAMMAR_LESSONS[2],
        GRAMMAR_LESSONS[3]
    ],
    "N4": [
        GRAMMAR_LESSONS[4],
        GRAMMAR_LESSONS[5],
        {
            "id": "tai_form",
            "title": "Lesson 3: Expressing Desire (~たい - tai)",
            "desc": "The ~たい form is used to express what you want to do. It conjugates like an i-adjective.",
            "concept": "Verb Stem + たい です (I want to do...)\nExample: 日本に行きたいです (I want to go to Japan).",
            "examples": [
                {"ja": "お寿司を食べたいです。", "romaji": "osushi o tabetai desu.", "en": "I want to eat sushi.", "pron": "おすしをたべたいです。"},
                {"ja": "日本に行きたいです。", "romaji": "nihon ni ikitai desu.", "en": "I want to go to Japan.", "pron": "にほん に いきたい です。"}
            ],
            "builder": {
                "english": "I want to eat sushi.",
                "correct_order": ["お寿司", "を", "食べたい", "です"],
                "options": ["お寿司", "が", "を", "食べたい", "です", "飲みます"]
            }
        },
        {
            "id": "te_iru",
            "title": "Lesson 4: Present Progressive (~ている - te iru)",
            "desc": "Using the te-form of a verb + いる expresses an ongoing action (like -ing in English) or state.",
            "concept": "Verb Te-form + いる / います\nExample: 本を読んでいる (I am reading a book).",
            "examples": [
                {"ja": "本を読んでいます。", "romaji": "hon o yondeimasu.", "en": "I am reading a book.", "pron": "ほんをよんでいます。"},
                {"ja": "雨が降っています。", "romaji": "ame ga futteimasu.", "en": "It is raining.", "pron": "あめがふっています。"}
            ],
            "builder": {
                "english": "I am reading a book.",
                "correct_order": ["本", "を", "読んで", "います"],
                "options": ["本", "が", "を", "読んで", "います", "飲みます"]
            }
        }
    ],
    "N3": [
        {
            "id": "koto_ga_dekiru",
            "title": "Lesson 1: Ability (ことができる - koto ga dekiru)",
            "desc": "Expresses ability or permission to do something by adding ことができる to the dictionary form of a verb.",
            "concept": "Verb Dict form + ことが できる / できます\nExample: 日本語を話すことができます (I can speak Japanese).",
            "examples": [
                {"ja": "日本語を話すことができます。", "romaji": "nihongo o hanasu koto ga dekimasu.", "en": "I can speak Japanese.", "pron": "にほんご を はなす こと が できます。"},
                {"ja": "泳ぐことができます。", "romaji": "oyogu koto ga dekimasu.", "en": "I can swim.", "pron": "およぐ ことが できます。"}
            ],
            "builder": {
                "english": "I can speak Japanese.",
                "correct_order": ["日本語", "を", "話す", "こと", "が", "できます"],
                "options": ["日本語", "を", "に", "話す", "こと", "が", "できます", "話します"]
            }
        },
        {
            "id": "sou_desu",
            "title": "Lesson 2: Conjecture / Appearance (~そうです - sou desu)",
            "desc": "Indicates that something looks like it is about to happen or has a certain quality, based on appearance.",
            "concept": "Verb stem / Adj (drop i/na) + そうです\nExample: 雨が降りそうです (It looks like it will rain).",
            "examples": [
                {"ja": "雨が降りそうです。", "romaji": "ame ga furisou desu.", "en": "It looks like it is going to rain.", "pron": "あめがふりそうです。"},
                {"ja": "美味しそうです。", "romaji": "oishisou desu.", "en": "It looks delicious.", "pron": "おいしそうです。"}
            ],
            "builder": {
                "english": "It looks delicious.",
                "correct_order": ["美味し", "そう", "です"],
                "options": ["美味し", "そう", "です", "くて", "な", "甘い"]
            }
        }
    ],
    "N2": [
        {
            "id": "ni_chigainai",
            "title": "Lesson 1: Strong Certainty (に違いない - ni chigainai)",
            "desc": "Used to express a strong, logical belief that something is without a doubt true.",
            "concept": "Noun/Verb/Adj Plain + に違いない / に違いありません\nExample: 彼は先生に違いない (He must be a teacher).",
            "examples": [
                {"ja": "彼は先生に違いない。", "romaji": "kare wa sensei ni chigainai.", "en": "He must be a teacher.", "pron": "かれはせんせいにちがいない。"},
                {"ja": "明日は雨に違いない。", "romaji": "ashita wa ame ni chigainai.", "en": "Tomorrow it will rain without a doubt.", "pron": "あしたはあめにちがいない。"}
            ],
            "builder": {
                "english": "He must be a teacher.",
                "correct_order": ["彼", "は", "先生", "に", "違いない"],
                "options": ["彼", "は", "が", "先生", "に", "違いない", "です"]
            }
        },
        {
            "id": "wake_ni_wa_ikanai",
            "title": "Lesson 2: Cannot Afford to (~わけにはいかない - wake ni wa ikanai)",
            "desc": "Indicates that due to social, moral, or situational circumstances, one cannot or must not perform an action.",
            "concept": "Verb Dict form + わけにはいかない\nExample: 休むわけにはいかない (I cannot afford to take a day off).",
            "examples": [
                {"ja": "休むわけにはいかない。", "romaji": "yasumu wake ni wa ikanai.", "en": "I cannot afford to take a day off.", "pron": "やすむわけにはいかない。"},
                {"ja": "負けるわけにはいかない。", "romaji": "makeru wake ni wa ikanai.", "en": "I cannot afford to lose.", "pron": "まけるわけにはいかない。"}
            ],
            "builder": {
                "english": "I cannot afford to take a day off.",
                "correct_order": ["休む", "わけ", "には", "いかない"],
                "options": ["休む", "こと", "わけ", "には", "いかない", "できません"]
            }
        }
    ],
    "N1": [
        {
            "id": "kagiri_da",
            "title": "Lesson 1: Extreme Emotion (限りだ - kagiri da)",
            "desc": "Expresses that a certain feeling or state is at its absolute peak or limit. Often used with emotional i/na-adjectives.",
            "concept": "Adjective + 限りだ / 限りです\nExample: 嬉しい限りです (I am extremely happy).",
            "examples": [
                {"ja": "嬉しい限りです。", "romaji": "ureshishi kagiri desu.", "en": "I am extremely happy.", "pron": "うれしいかぎりです。"},
                {"ja": "残念な限りです。", "romaji": "zannen na kagiri desu.", "en": "It is extremely regrettable.", "pron": "ざんねんなかぎりです。"}
            ],
            "builder": {
                "english": "I am extremely happy.",
                "correct_order": ["嬉しい", "限り", "です"],
                "options": ["嬉しい", "限り", "です", "そう", "とても", "楽しむ"]
            }
        },
        {
            "id": "wo_mochiite",
            "title": "Lesson 2: Utilizing / By Means Of (~を用いて - o mochiite)",
            "desc": "A highly formal business phrase meaning to make use of or utilize a resource/tool to accomplish a task.",
            "concept": "Noun + を用いて + Action\nExample: 最新技術を用いて開発する (Develop using the latest technology).",
            "examples": [
                {"ja": "最新技術を用いて開発する。", "romaji": "saishin gijutsu o mochiite kaihatsu suru.", "en": "Develop utilizing the latest technology.", "pron": "さいしんぎじゅつをもちいてかいはつする。"},
                {"ja": "データを用いて説明します。", "romaji": "deeta o mochiite setsumei shimasu.", "en": "I will explain using the data.", "pron": "でーたをもちいてせつめいします。"}
            ],
            "builder": {
                "english": "I will explain using the data.",
                "correct_order": ["データ", "を", "用いて", "説明", "します"],
                "options": ["データ", "を", "に", "用いて", "説明", "します", "使います"]
            }
        }
    ]
}

# ==================== PRE-DEFINED OFFLINE CONVERSATION SIMULATOR TREES ====================
OFFLINE_CONVERSATION_TREES = {
    "At a Japanese Restaurant": {
        "start": {
            "ai_reply": "いらっしゃいませ！レストランへようこそ。ご注文はお決まりですか？",
            "ai_yomi": "いらっしゃいませ！ れすとらん へ ようこそ。 ごちゅうもん は おきまり です か？",
            "ai_romaji": "irasshaimase! resutoran e yokoso. gochuumon wa okimari desu ka?",
            "ai_en": "Welcome! Welcome to the restaurant. Have you decided on your order?",
            "ai_explain": "### 💡 Grammar & Structure\n- **いらっしゃいませ！ (Irasshaimase)**: A polite greeting used by shop/restaurant staff to welcome customers. Derived from the honorific verb いらっしゃる.\n- **ようこそ (Yookoso)**: Welcoming phrase, preceded by [location] + へ.\n- **ご注文はお決まりですか (Gochuumon wa okimari desu ka)**: 'Have you decided on your order?' Uses polite prefixes ご- and お-.\n\n### 📖 Vocabulary & Readings\n1. **ご注文 (ごちゅうもん - Gochuumon)**: Order (n.)\n2. **決まり (きまり - Kimari)**: Decision / set (n.)\n3. **レストラン (Resutoran)**: Restaurant (n.)\n\n### 📌 Particles Used\n- **へ (e)**: Directional particle indicating the destination.\n- **は (wa)**: Topic marker particle.\n- **か (ka)**: Question particle at the end.\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Keigo (Respectful hospitality language).",
            "choices": [
                {
                    "text": "メニューをください。",
                    "en": "Please give me the menu.",
                    "next_node": "ask_menu"
                },
                {
                    "text": "おすすめは何ですか。",
                    "en": "What is the recommendation?",
                    "next_node": "ask_recommend"
                }
            ]
        },
        "ask_menu": {
            "ai_reply": "はい、どうぞ！当店のおすすめは特製ラーメンと新鮮な寿司です。",
            "ai_yomi": "はい、 どうぞ！ とうてん の おすすめ は とくせい らーめん と しんせん な すし です。",
            "ai_romaji": "hai, douzo! touten no osusume wa tokusei ramen to shinsen na sushi desu.",
            "ai_en": "Here you go! Our recommendation is the special ramen and fresh sushi.",
            "ai_explain": "### 💡 Grammar & Structure\n- **はい、どうぞ！ (Hai, douzo)**: 'Yes, here you go!' Used when handing things over.\n- **おすすめはラーメンと寿司です (Osusume wa raamen to sushi desu)**: 'The recommendation is ramen and sushi.'\n\n### 📖 Vocabulary & Readings\n1. **当店 (とうてん - Touten)**: Our shop (n.)\n2. **おすすめ (Osusume)**: Recommendation (n.)\n3. **特製 (とくせい - Tokusei)**: Special / deluxe (n.)\n4. **新鮮な (しんせんな - Shinsenna)**: Fresh (Na-adj.)\n5. **お寿司 (おすし - Osushi)**: Sushi (n., polite prefix お-)\n\n### 📌 Particles Used\n- **の (no)**: Possessive particle (当店のおすすめ).\n- **は (wa)**: Topic marker.\n- **と (to)**: Coordinating particle meaning 'and'.\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Standard polite (Teineigo) using です.",
            "choices": [
                {
                    "text": "じゃあ、ラーメンをください。",
                    "en": "Then, ramen please.",
                    "next_node": "order_ramen"
                },
                {
                    "text": "お寿司をお願いします。",
                    "en": "Sushi please.",
                    "next_node": "order_sushi"
                }
            ]
        },
        "ask_recommend": {
            "ai_reply": "本日のおすすめは特製ラーメンです。醤油と味噌があります。",
            "ai_yomi": "ほんじつ の おすすめ は とくせい らーめん です。 しょうゆ と みそ が あります。",
            "ai_romaji": "honjitsu no osusume wa tokusei ramen desu. shouyu to miso ga arimasu.",
            "ai_en": "Today's recommendation is the special ramen. We have soy sauce and miso flavor.",
            "ai_explain": "### 💡 Grammar & Structure\n- **本日のおすすめは特製ラーメンです (Honjitsu no osusume wa tokusei ramen desu)**: 'Today's recommendation is the special ramen.'\n- **醤油と味噌があります (Shouyu to miso ga arimasu)**: 'We have soy sauce and miso.' Uses the existence verb あります.\n\n### 📖 Vocabulary & Readings\n1. **本日 (ほんじつ - Honjitsu)**: Today (formal alternative to 今日 kyou).\n2. **醤油 (しょうゆ - Shouyu)**: Soy sauce (n.)\n3. **味噌 (みそ - Miso)**: Fermented soybean paste (n.)\n\n### 📌 Particles Used\n- **の (no)**: Connecting particle (本日のおすすめ).\n- **と (to)**: Meaning 'and'.\n- **が (ga)**: Subject marker particle indicating what exists (arimasu).\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Standard polite using です and あります.",
            "choices": [
                {
                    "text": "醤油ラーメンをください。",
                    "en": "Soy sauce ramen please.",
                    "next_node": "order_ramen"
                },
                {
                    "text": "お水をください。",
                    "en": "Please give me water.",
                    "next_node": "ask_water"
                }
            ]
        },
        "order_ramen": {
            "ai_reply": "かしこまりました！特製ラーメンですね。少々お待ちください。",
            "ai_yomi": "かしこまりました！ とくせい らーめん です ね。 しょうしょう おまち ください。",
            "ai_romaji": "kashikomarimashita! tokusei ramen desu ne. shoushou omachi kudasai.",
            "ai_en": "Certainly! Special ramen, correct. Please wait a moment.",
            "ai_explain": "### 💡 Grammar & Structure\n- **かしこまりました (Kashikomarimashita)**: A humble verb meaning 'Understood / Certainly'. Extremely polite equivalent of わかりました.\n- **少々お待ちください (Shoushou omachi kudasai)**: 'Please wait a moment.' Respectful request formula (お- + verb stem + ください).\n\n### 📖 Vocabulary & Readings\n1. **かしこまりました**: Certainly / I understand (humble verb).\n2. **少々 (しょうしょう - Shoushou)**: A little / a moment (formal adverb).\n3. **待ち (まち - Machi)**: Wait (noun/stem of 待つ matsu).\n\n### 📌 Particles Used\n- **ね (ne)**: Agreement seeker particle (特製ラーメンですね).\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Kenjougo (Humble) and Sonkeigo (Respectful) combined for high-end hospitality.",
            "choices": [
                {
                    "text": "はい、楽しみにしています。",
                    "en": "Yes, I am looking forward to it.",
                    "next_node": "end_convo"
                }
            ]
        },
        "order_sushi": {
            "ai_reply": "かしこまりました！新鮮なお寿司です。お飲み物はいかがですか？",
            "ai_yomi": "かしこまりました！ しんせん な おすし です。 おのみもの は いかが です か？",
            "ai_romaji": "kashikomarimashita! shinsen na osushi desu. onomimono wa ikaga desu ka?",
            "ai_en": "Certainly! Fresh sushi. Would you like something to drink?",
            "ai_explain": "### 💡 Grammar & Structure\n- **かしこまりました (Kashikomarimashita)**: 'Certainly'. Extremely polite/humble response.\n- **お飲み物はいかがですか (Onomimono wa ikaga desu ka)**: 'Would you like something to drink?' polite offer pattern.\n\n### 📖 Vocabulary & Readings\n1. **新鮮な (しんせんな - Shinsenna)**: Fresh (Na-adj.)\n2. **お飲み物 (おのみもの - Onomimono)**: Beverage (n., with polite prefix お-)\n3. **いかが (Ikaga)**: How / what about (polite equivalent of どう dou)\n\n### 📌 Particles Used\n- **は (wa)**: Topic marker.\n- **か (ka)**: Question marker.\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Extremely polite customer-service Japanese.",
            "choices": [
                {
                    "text": "お茶をください。",
                    "en": "Green tea please.",
                    "next_node": "tea_done"
                },
                {
                    "text": "いいえ、大丈夫です。",
                    "en": "No, I am fine.",
                    "next_node": "end_convo"
                }
            ]
        },
        "tea_done": {
            "ai_reply": "温かいお茶ですね、ただいまお持ちします！",
            "ai_yomi": "あたたかい おちゃ です ね、 ただいま おもち します！",
            "ai_romaji": "atakai ocha desu ne, tadaima omochi shimasu!",
            "ai_en": "Warm green tea, correct. I'll bring it right away!",
            "ai_explain": "### 💡 Grammar & Structure\n- **温かいお茶ですね (Atatakai ocha desu ne)**: 'Warm green tea, correct?'\n- **ただいまお持ちします (Tadaima omochi shimasu)**: 'I will bring it right away!' Humble action pattern (お + verb stem + します).\n\n### 📖 Vocabulary & Readings\n1. **温かい (あたたかい - Atatakai)**: Warm (I-adj.)\n2. **お茶 (おちゃ - Ocha)**: Green tea (n., polite prefix お-)\n3. **ただいま (Tadaima)**: Right now / immediately (formal adverb).\n4. **お持ちします (おもちします - Omochi shimasu)**: Bring (humble verb format of 持つ).\n\n### 📌 Particles Used\n- **ね (ne)**: Tag-question / confirmation particle.\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Humble language (Kenjougo). Standard polite restaurant response.",
            "choices": [
                {
                    "text": "ありがとう。",
                    "en": "Thank you.",
                    "next_node": "end_convo"
                }
            ]
        },
        "ask_water": {
            "ai_reply": "はい、お冷をお持ちします。ご注文は他によろしいですか？",
            "ai_yomi": "はい、 おひや を おもち します。 ごちゅうもん は ほか に よろしい です か？",
            "ai_romaji": "hai, ohiya o omochi shimasu. gochuumon wa hoka ni yoroshii desu ka?",
            "ai_en": "Yes, I'll bring cold water. Is there anything else you would like to order?",
            "ai_explain": "### 💡 Grammar & Structure\n- **お冷をお持ちします (Ohiya o omochi shimasu)**: 'I will bring cold water.' Humble action pattern (お + verb stem + します).\n- **ご注文は他によろしいですか (Gochuumon wa hoka ni yoroshii desu ka)**: 'Is there anything else you would like to order?'\n\n### 📖 Vocabulary & Readings\n1. **お冷 (おひや - Ohiya)**: Cold drinking water (n., polite/respectful term used in restaurants).\n2. **他に (ほかに - Hoka ni)**: Other / besides (adverb).\n3. **よろしい (Yoroshii)**: Good / acceptable (polite equivalent of いい ii).\n\n### 📌 Particles Used\n- **を (o)**: Object marker particle.\n- **は (wa)**: Topic marker.\n- **に (ni)**: Particle indicating addition/direction.\n- **か (ka)**: Question particle.\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Respectful restaurant language. Uses 'お冷' (ohiya) which is a standard Japanese dining custom.",
            "choices": [
                {
                    "text": "以上で大丈夫です。",
                    "en": "That's all, thank you.",
                    "next_node": "end_convo"
                }
            ]
        },
        "end_convo": {
            "ai_reply": "ごゆっくりどうぞ！何かありましたらお呼びください。",
            "ai_yomi": "ごゆっくり どうぞ！ なにか ありましたら および ください。",
            "ai_romaji": "goyukkuri douzo! nanika arimashitara oyobi kudasai.",
            "ai_en": "Please enjoy! Please call me if you need anything.",
            "ai_explain": "### 💡 Grammar & Structure\n- **ごゆっくりどうぞ (Goyukkuri douzo)**: 'Please enjoy / take your time.' Polite welcoming invitation.\n- **何かありましたらお呼びください (Nanika arimashitara oyobi kudasai)**: 'Please call me if there is anything.' Respectful request form.\n\n### 📖 Vocabulary & Readings\n1. **ゆっくり (Yukkuri)**: Slowly / at ease (adv., prefixed with polite ご-).\n2. **呼び (よび - Yobi)**: Call (stem of 呼ぶ yobu).\n3. **ありましたら**: If there exists (polite conditional form of ある aru).\n\n### 📌 Particles Used\n- **か (ka)**: Indefinite particle (何か nanika = something).\n- **ら (ra)**: Conditional marker (〜たら -tara = if/when).\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Highly polite and welcoming service Japanese.",
            "choices": []
        }
    },
    "Asking for Directions": {
        "start": {
            "ai_reply": "はい、何でしょうか？何かお困りですか？",
            "ai_yomi": "はい、 なん でしょう か？ なにか おこまり です か？",
            "ai_romaji": "hai, nan deshou ka? nanika okomari desu ka?",
            "ai_en": "Yes, what is it? Are you having some trouble?",
            "ai_explain": "### 💡 Grammar & Structure\n- **何でしょうか (Nan deshou ka)**: 'What is it?' polite expression.\n- **何かお困りですか (Nanika okomari desu ka)**: 'Are you having some trouble?'\n  - **お- + verb stem + です (o- + stem + desu)**: Polite form to state someone else's state or action.\n\n### 📖 Vocabulary & Readings\n1. **何か (なにか - Nanika)**: Something (pronoun).\n2. **お困り (おこまり - Okomari)**: Trouble / in difficulty (n., stem of 困る komaru with polite お-).\n\n### 📌 Particles Used\n- **か (ka)**: Question particle at the end of both questions.\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Standard polite Japanese. Helpful and friendly stranger tone.",
            "choices": [
                {
                    "text": "すみません、駅はどこですか。",
                    "en": "Excuse me, where is the station?",
                    "next_node": "ask_station"
                },
                {
                    "text": "近くにコンビニはありますか。",
                    "en": "Is there a convenience store nearby?",
                    "next_node": "ask_conbini"
                }
            ]
        },
        "ask_station": {
            "ai_reply": "駅ですね。この道をまっすぐ行って、最初の交差点を右に曲がってください。",
            "ai_yomi": "えき です ね。 この みち を まっすぐ いって、 さいしょ の こうさてん を みぎ に まがって ください。",
            "ai_romaji": "eki desu ne. kono michi o massugu itte, saisho no kousaten o migi ni magatte kudasai.",
            "ai_en": "The station, correct. Go straight down this street, and turn right at the first intersection.",
            "ai_explain": "### 💡 Grammar & Structure\n- **駅ですね (Eki desu ne)**: 'The station, correct?'\n- **この道をまっすぐ行って (Kono michi o massugu itte)**: 'Go straight down this street...'\n  - **行って (itte)**: Te-form of 行く (iku - to go), used to connect instructions sequentially.\n- **曲がってください (Magatte kudasai)**: 'Please turn...'\n  - **[Verb Te-form] + ください (kudasai)**: Standard request pattern.\n\n### 📖 Vocabulary & Readings\n1. **駅 (えき - Eki)**: Station (n.)\n2. **道 (みち - Michi)**: Street / road (n.)\n3. **まっすぐ (Massugu)**: Straight ahead (adv.)\n4. **最初 (さいしょ - Saisho)**: First (n.)\n5. **交差点 (こうさてん - Kousaten)**: Intersection (n.)\n6. **右 (みぎ - Migi)**: Right (direction) (n.)\n7. **曲がり (まがり - Magari)**: Turn (stem of 曲がる magaru).\n\n### 📌 Particles Used\n- **を (o)**: Object marker indicating the path walked along (道を).\n- **に (ni)**: Directional particle indicating the direction of the turn (右に).\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Standard polite request. Standard street directions tone.",
            "choices": [
                {
                    "text": "歩いて何分くらいですか。",
                    "en": "How many minutes on foot?",
                    "next_node": "station_minutes"
                },
                {
                    "text": "ありがとうございます！",
                    "en": "Thank you very much!",
                    "next_node": "end_convo"
                }
            ]
        },
        "station_minutes": {
            "ai_reply": "歩いて五分くらいですよ。とても近いです。",
            "ai_yomi": "あるいて ごふん くらい です よ。 とても ちかい です。",
            "ai_romaji": "aruite gofun kurai desu yo. totemo chikai desu.",
            "ai_en": "It is about 5 minutes on foot. It is very close.",
            "ai_explain": "### 💡 Grammar & Structure\n- **歩いて五分くらいですよ (Aruite gofun kurai desu yo)**: 'It's about five minutes on foot, you know.'\n  - **歩いて (aruite)**: Te-form of 歩く (aruku - to walk), used adverbially as 'on foot'.\n  - **五分くらい (gofun kurai)**: 'About five minutes'.\n- **とても近いです (Totemo chikai desu)**: 'It is very close.'\n\n### 📖 Vocabulary & Readings\n1. **歩く (あるく - Aruku)**: Walk (v.)\n2. **五分 (ごふん - Gofun)**: 5 minutes (counter word).\n3. **くらい (Kurai)**: Approximately / about (suffix).\n4. **とても (Totemo)**: Very (adv.)\n5. **近い (ちかい - Chikai)**: Close / near (I-adj.)\n\n### 📌 Particles Used\n- **よ (yo)**: Assuring/informative sentence-ending particle.\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Standard polite. Warm and helpful tone.",
            "choices": [
                {
                    "text": "助かりました。ありがとうございます！",
                    "en": "That helped a lot. Thank you!",
                    "next_node": "end_convo"
                }
            ]
        },
        "ask_conbini": {
            "ai_reply": "はい、あそこの角を左に曲がると、ローソンがありますよ。",
            "ai_yomi": "はい、 あそこ の かど を ひだり に まがる と、 ろーそん が あります よ。",
            "ai_romaji": "hai, asoko no kado o hidari ni magaru to, rooson ga arimasu yo.",
            "ai_en": "Yes, if you turn left at that corner over there, there is a Lawson.",
            "ai_explain": "### 💡 Grammar & Structure\n- **あそこの角を左に曲がると (Asoko no kado o hidari ni magaru to)**: 'If you turn left at that corner over there...'\n  - **曲がると (magaru to)**: Verb dictionary form + と, indicating a natural conditional/consequence ('if you do [X], then [Y] happens').\n- **ローソンがありますよ (Rooson ga arimasu yo)**: 'There is a Lawson.'\n\n### 📖 Vocabulary & Readings\n1. **あそこ (Asoko)**: Over there (demonstrative pronoun).\n2. **角 (かど - Kado)**: Corner (n.)\n3. **左 (ひだり - Hidari)**: Left (direction) (n.)\n4. **ローソン (Rooson)**: Lawson (popular Japanese convenience store chain) (n.)\n\n### 📌 Particles Used\n- **の (no)**: Connecting pronoun and corner (あそこの角).\n- **を (o)**: Indicating the space through which one turns (角を).\n- **に (ni)**: Direction of turning (左に).\n- **が (ga)**: Subject of existence (ローソンが).\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Standard polite with conditional 'と' (to).",
            "choices": [
                {
                    "text": "ATMはありますか。",
                    "en": "Is there an ATM?",
                    "next_node": "conbini_atm"
                },
                {
                    "text": "ありがとうございます。",
                    "en": "Thank you.",
                    "next_node": "end_convo"
                }
            ]
        },
        "conbini_atm": {
            "ai_reply": "はい、そのローソンの中に銀行のATMがありますよ。",
            "ai_yomi": "はい、 その ろーそん の なか に ぎんこう の ATM が あります よ。",
            "ai_romaji": "hai, sono rooson no naka ni ginkou no ATM ga arimasu yo.",
            "ai_en": "Yes, there is a bank ATM inside that Lawson.",
            "ai_explain": "### 💡 Grammar & Structure\n- **そのローソンの中に (Sono rooson no naka ni)**: 'Inside that Lawson...'\n- **銀行のATMがありますよ (Ginkou no ATM ga arimasu yo)**: 'There is a bank ATM.'\n\n### 📖 Vocabulary & Readings\n1. **中 (なか - Naka)**: Inside (n.)\n2. **銀行 (ぎんこう - Ginkou)**: Bank (n.)\n3. **ATM (エーティーエム - Eetiiemu)**: ATM (n.)\n\n### 📌 Particles Used\n- **の (no)**: Connecting 'Lawson' and 'inside' (ローソンの中), and 'bank' and 'ATM' (銀行 of ATM).\n- **に (ni)**: Location of existence particle.\n- **が (ga)**: Subject marker for あります.\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Polite. Helpful follow-up details.",
            "choices": [
                {
                    "text": "わかりました！行ってみます。",
                    "en": "I understand! I will go check it out.",
                    "next_node": "end_convo"
                }
            ]
        },
        "end_convo": {
            "ai_reply": "いえいえ、お気をつけて行ってくださいね！",
            "ai_yomi": "いえいえ、 おき を つけて いって ください ね！",
            "ai_romaji": "ieie, oki o tsukete itte kudasai ne!",
            "ai_en": "No problem, please take care and have a safe trip!",
            "ai_explain": "### 💡 Grammar & Structure\n- **いえいえ (Ieie)**: 'No, not at all!' Standard friendly way to brush off a thank you.\n- **お気をつけて行ってくださいね (Oki o tsukete itte kudasai ne)**: 'Please go carefully.' Respectful safety parting phrase.\n  - **気をつける (ki o tsukeru)**: 'To pay attention / be careful'.\n\n### 📖 Vocabulary & Readings\n1. **気 (き - Ki)**: Spirit / mind (n.)\n2. **気をつける (きをつける - Ki o tsukeru)**: Be careful (compound verb).\n3. **行って (いって - Itte)**: Te-form of 行く (iku - to go).\n\n### 📌 Particles Used\n- **お- (o-)**: Polite prefix attached to '気' (ki).\n- **を (o)**: Object marker.\n- **ね (ne)**: Softening/friendly sentence-ending particle.\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Standard polite. Shows typical Japanese customer-first hospitality or friendly concern.",
            "choices": []
        }
    },
    "Checking in at a Hotel": {
        "start": {
            "ai_reply": "いらっしゃいませ。帝国ホテルへようこそ。チェックインでございますか？",
            "ai_yomi": "いらっしゃいませ。 ていこく ほてる へ ようこそ。 ちぇっくいん で ございます か？",
            "ai_romaji": "irasshaimase. teikoku hoteru e yokoso. chekkuin de gozaimasu ka?",
            "ai_en": "Welcome. Welcome to the Imperial Hotel. Are you checking in?",
            "ai_explain": "### 💡 Grammar & Structure\n- **いらっしゃいませ (Irasshaimase)**: Standard shop greeting.\n- **チェックインでございますか (Chekkuin de gozaimasu ka)**: 'Are you checking in?'\n  - **でございます (de gozaimasu)**: Humble/highly polite equivalent of です (desu).\n\n### 📖 Vocabulary & Readings\n1. **帝国ホテル (ていこくほてる - Teikoku Hoteru)**: Imperial Hotel (n.)\n2. **チェックイン (Chekkuin)**: Check-in (n.)\n\n### 📌 Particles Used\n- **へ (e)**: Direction particle.\n- **か (ka)**: Question particle.\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Keigo / Teineigo. Highly formal hospitality suited for prestigious hotels.",
            "choices": [
                {
                    "text": "はい、チェックインをお願いします。",
                    "en": "Yes, check-in please.",
                    "next_node": "check_in"
                }
            ]
        },
        "check_in": {
            "ai_reply": "かしこまりました。ご予約のお名前をカタカナでお願いいたします。",
            "ai_yomi": "かしこまりました。 ごよやく の おなまえ を かたかな で おねがい いたします。",
            "ai_romaji": "kashikomarimashita. goyoyaku no onamae o katakana de onegai itashimasu.",
            "ai_en": "Certainly. Could I have the name on your reservation in Katakana?",
            "ai_explain": "### 💡 Grammar & Structure\n- **ご予約のお名前 (Goyoyaku no onamae)**: 'Your reservation name'. Respectful prefixes ご- and お-.\n- **お願いいたします (Onegai itashimasu)**: 'Please / I humbly request.' Humble equivalent of お願いします.\n\n### 📖 Vocabulary & Readings\n1. **予約 (よやく - Yoyaku)**: Reservation (n.)\n2. **名前 (なまえ - Namae)**: Name (n.)\n3. **カタカナ (Katakana)**: Katakana script (n.)\n4. **お願いいたします (おねがいいたします - Onegai itashimasu)**: Humbly request (humble verb).\n\n### 📌 Particles Used\n- **の (no)**: Connects reservation and name.\n- **を (o)**: Object marker for naming (お名前を).\n- **de (de)**: Instrumental particle meaning 'by / using' (カタカナで).\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Kenjougo (Humble). Extremely polite Japanese concierge style.",
            "choices": [
                {
                    "text": "スミスです。",
                    "en": "I am Smith.",
                    "next_node": "smith_booking"
                },
                {
                    "text": "予約はありません。空室はありますか。",
                    "en": "No reservation. Do you have vacancies?",
                    "next_node": "no_booking"
                }
            ]
        },
        "smith_booking": {
            "ai_reply": "スミス様ですね。はい、二泊のご予約を確認いたしました。こちらが鍵でございます。",
            "ai_yomi": "すみす さま です ね。 はい、 にはく の ごよやく を かくにん いたしました。 こちら が かぎ で ございます。",
            "ai_romaji": "sumisu sama desu ne. hai, nihaku no goyoyaku o kakunin itashimaishita. kochira ga kagi de gozaimasu.",
            "ai_en": "Mr./Ms. Smith, correct. Yes, I have confirmed your 2-night stay reservation. Here is your key.",
            "ai_explain": "### 💡 Grammar & Structure\n- **スミス様ですね (Sumisu-sama desu ne)**: 'Mr./Ms. Smith, correct?'\n  - **様 (さま - sama)**: Respectful title suffix, much more polite than さん (san).\n- **二泊のご予約を確認いたしました (Nihaku no goyoyaku o kakunin itashimashita)**: 'I have confirmed your reservation for two nights.'\n  - **いたしました (itashimashita)**: Humble form of しました (did).\n\n### 📖 Vocabulary & Readings\n1. **二泊 (にはく - Nihaku)**: Two nights stay (counter word).\n2. **確認 (かくにん - Kakunin)**: Confirmation (n./v.)\n3. **鍵 (かぎ - Kagi)**: Key (n.)\n4. **ございます (Gozaimasu)**: Polite equivalent of あります.\n\n### 📌 Particles Used\n- **の (no)**: Connecting stay duration and reservation (二泊のご予約).\n- **を (o)**: Object of confirmation (ご予約を).\n- **が (ga)**: Subject marker indicating the key (こちらが).\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Highly respectful hotel concierge language.",
            "choices": [
                {
                    "text": "朝食の時間は何時ですか。",
                    "en": "What time is breakfast?",
                    "next_node": "breakfast_time"
                },
                {
                    "text": "Wi-Fiはありますか。",
                    "en": "Is there Wi-Fi?",
                    "next_node": "wifi_info"
                }
            ]
        },
        "no_booking": {
            "ai_reply": "申し訳ございません。本日は満室でございます。",
            "ai_yomi": "もうしわけ ございません。 ほんじつ は まんしつ で ございます。",
            "ai_romaji": "moushiwake gozaimasen. honjitsu wa manshitsu de gozaimasu.",
            "ai_en": "I am deeply sorry. Today we are fully booked.",
            "ai_explain": "### 💡 Grammar & Structure\n- **申し訳ございません (Moushiwake gozaimasen)**: 'I am deeply sorry.' The standard highly formal apology in Japanese.\n- **満室でございます (Manshitsu de gozaimasu)**: 'We are fully booked.' Uses formal でございます.\n\n### 📖 Vocabulary & Readings\n1. **申し訳 (もうしわけ - Moushiwake)**: Excuse / apology (n.)\n2. **満室 (まんしつ - Manshitsu)**: Full rooms / no occupancy (n.)\n\n### 📌 Particles Used\n- **は (wa)**: Topic marker.\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Max politeness Keigo. Shows deep regret and apology.",
            "choices": [
                {
                    "text": "そうですか。残念です。",
                    "en": "I see. That's unfortunate.",
                    "next_node": "end_convo"
                }
            ]
        },
        "breakfast_time": {
            "ai_reply": "朝食は一階のレストランで朝七時から十時までとなっております。",
            "ai_yomi": "ちょうしょく は いっかい の れすとらん で あさ しちじ から じゅうじ まで と なって おります。",
            "ai_romaji": "choushoku wa ikkai no resutoran de asa shichiji kara juuji made to natte orimasu.",
            "ai_en": "Breakfast is on the first floor restaurant from 7 AM to 10 AM.",
            "ai_explain": "### 💡 Grammar & Structure\n- **朝七時から十時まで (Asa shichiji kara juuji made)**: 'From 7:00 AM to 10:00 AM'.\n  - **から (kara) & まで (made)**: 'From' and 'To' time range markers.\n- **となっております (to natte orimasu)**: 'It has been decided/set as...' extremely polite equivalent of となっています.\n\n### 📖 Vocabulary & Readings\n1. **朝食 (ちょうしょく - Choushoku)**: Breakfast (n.)\n2. **一階 (いっかい - Ikkai)**: First floor (n.)\n3. **朝 (あさ - Asa)**: Morning (n.)\n4. **七時 (しちじ - Shichiji)**: 7 o'clock (counter word).\n5. **十時 (じゅうじ - Juuji)**: 10 o'clock (counter word).\n\n### 📌 Particles Used\n- **は (wa)**: Topic marker.\n- **の (no)**: Location modifier (一階のレストラン).\n- **で (de)**: Location of action particle (レストランで).\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Highly polite service Japanese.",
            "choices": [
                {
                    "text": "ありがとうございます。部屋に行きます。",
                    "en": "Thank you. I'll head to my room.",
                    "next_node": "end_convo"
                }
            ]
        },
        "wifi_info": {
            "ai_reply": "はい、お部屋で無料Wi-Fiが使えます。パスワードは鍵のカバーに書いてあります。",
            "ai_yomi": "はい、 おへや で むりょう Wi-Fi が つかえます。 ぱすわーど は かぎ の かばー に かいて あります。",
            "ai_romaji": "hai, oheya de muryou Wi-Fi ga tsukaemasu. pasuwaado wa kagi no kabaa ni kaite arimasu.",
            "ai_en": "Yes, free Wi-Fi is available in your room. The password is written on the key cover.",
            "ai_explain": "### 💡 Grammar & Structure\n- **無料Wi-Fiが使えます (Muryou Wi-Fi ga tsukaemasu)**: 'Free Wi-Fi is usable.'\n  - **使えます (tsukaemasu)**: Potential form of 使う (tsukau - to use), meaning 'can use / is usable'.\n- **書いてあります (Kaite arimasu)**: 'It is written.' State pattern (Te-form + あります) representing an action performed in the past whose results remain.\n\n### 📖 Vocabulary & Readings\n1. **無料 (むりょう - Muryou)**: Free of charge (n.)\n2. **使う (つかう - Tsukau)**: Use (v.)\n3. **パスワード (Pasuwaado)**: Password (n.)\n4. **カバー (Kabaa)**: Cover (n.)\n5. **書く (かく - Kaku)**: Write (v.)\n\n### 📌 Particles Used\n- **で (de)**: Location of availability (お部屋で).\n- **が (ga)**: Subject marker for potential verb (Wi-Fiが).\n- **は (wa)**: Topic marker.\n- **in (ni)**: Target of writing location (カバーに).\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Standard polite. Informative and polite hotel clerk tone.",
            "choices": [
                {
                    "text": "わかりました！ありがとうございます。",
                    "en": "Understood! Thank you very much.",
                    "next_node": "end_convo"
                }
            ]
        },
        "end_convo": {
            "ai_reply": "ごゆっくりお過ごしくださいませ。素晴らしいご滞在を！",
            "ai_yomi": "ごゆっくり おすごし くださいませ。 すばらしい ごたいざい を！",
            "ai_romaji": "goyukkuri osugoshi kudasaimase. subarashii gotaizai o!",
            "ai_en": "Please enjoy your stay with us. Have a wonderful stay!",
            "ai_explain": "### 💡 Grammar & Structure\n- **お過ごしくださいませ (Osugoshi kudasaimase)**: 'Please spend your time / stay.' Polite honorific request.\n  - **過ごす (sugosu)**: 'To spend time'. prefixed with お- and followed by honorific request くださいませ.\n- **素晴らしいご滞在を！ (Subarashii gotaizai o!)**: 'Have a wonderful stay!' (The verb 'have/enjoy' is politely omitted but implied).\n\n### 📖 Vocabulary & Readings\n1. **過ごす (すごす - Sugosu)**: Spend time / pass time (v.)\n2. **素晴らしい (すばらしい - Subarashii)**: Wonderful (I-adj.)\n3. **滞在 (たいざい - Taizai)**: Stay / visit (n., prefixed with polite ご-).\n\n### 📌 Particles Used\n- **を (o)**: Object marker pointing to the implied verb of wishing (素晴らしいご滞在を).\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Max hospitality Keigo. Warm wishing parting statement.",
            "choices": []
        }
    },
    "Casual Talk with Friends": {
        "start": {
            "ai_reply": "ヤッホー！最近どう？元気にしてる？",
            "ai_yomi": "ヤッホー！ さいきん どう？ げんき に してる？",
            "ai_romaji": "yahhoo! saikin dou? genki ni shiteru?",
            "ai_en": "Hey! How's it going lately? Are you doing well?",
            "ai_explain": "### 💡 Grammar & Structure\n- **ヤッホー！ (Yahhoo)**: Casual hello / hi! Used strictly between close friends.\n- **最近どう？ (Saikin dou?)**: 'How are you lately / How have things been?' Casual equivalent of いかがですか.\n- **元気にしてる？ (Genki ni shiteru?)**: 'Are you doing well / keeping active?' Casual equivalent of 元気にしていますか.\n\n### 📖 Vocabulary & Readings\n1. **最近 (さいきん - Saikin)**: Recently / lately (n.)\n2. **どう (Dou)**: How (adv.)\n3. **元気 (げんき - Genki)**: Healthy / energetic (Na-adj./n.)\n\n### 📌 Particles Used\n- **に (ni)**: Adverbial marker transforming '元気' into 'genki ni' (energetically / healthily).\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Casual / Informal (Tameguchi). Absolutely zero Keigo, standard friendly speech.",
            "choices": [
                {
                    "text": "元気だよ！そっちは？",
                    "en": "I'm doing well! How about you?",
                    "next_node": "friend_well"
                },
                {
                    "text": "ちょっと疲れているんだ。",
                    "en": "I'm a little bit tired.",
                    "next_node": "friend_tired"
                }
            ]
        },
        "friend_well": {
            "ai_reply": "私も絶好調！ねえ、今週末空いてる？遊びに行かない？",
            "ai_yomi": "わたし も ぜっこうちょう！ ねえ、 こんしゅうまつ あいてる？ あそび に いかない？",
            "ai_romaji": "watashi mo zekkouchou! nee, konshuumatsu aiteru? asobi ni ikanai?",
            "ai_en": "I'm in top shape too! Hey, are you free this weekend? Want to go hang out?",
            "ai_explain": "### 💡 Grammar & Structure\n- **私も絶好調！ (Watashi mo zekkouchou!)**: 'I'm also doing fantastic!'\n- **空いてる？ (Aiteru?)**: 'Are you free/open?' Shortened from 空いていますか.\n- **遊びに行かない？ (Asobi ni ikanai?)**: 'Do you want to hang out?' Casual invitation pattern (negative question form equivalent of 行きませんか).\n\n### 📖 Vocabulary & Readings\n1. **絶好調 (ぜっこうちょう - Zekkouchou)**: In perfect form / top shape (n.)\n2. **今週末 (こんしゅうまつ - Konshuumatsu)**: This weekend (n.)\n3. **遊ぶ (あそぶ - Asobu)**: Play / hang out (v.)\n\n### 📌 Particles Used\n- **も (mo)**: Particle meaning 'also / too' (私も).\n- **に (ni)**: Purpose particle indicating the goal of going (遊びに = for playing/hanging out).\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Friendly informal. Excited tone indicated by exclamation marks and casual negative-question invites.",
            "choices": [
                {
                    "text": "空いてるよ！どこに行く？",
                    "en": "I'm free! Where should we go?",
                    "next_node": "friend_plan"
                },
                {
                    "text": "ごめん、今週末は忙しいんだ。",
                    "en": "Sorry, I'm busy this weekend.",
                    "next_node": "friend_busy"
                }
            ]
        },
        "friend_tired": {
            "ai_reply": "えっ、大丈夫？仕事が忙しいの？無理しないでね。",
            "ai_yomi": "えっ、 だいじょうぶ？ しごと が いそがしい の？ むり しないで ね。",
            "ai_romaji": "e, daijoubu? shigoto ga isogashii no? muri shinaide ne.",
            "ai_en": "Oh, are you okay? Are you busy with work? Don't push yourself too hard.",
            "ai_explain": "### 💡 Grammar & Structure\n- **仕事が忙しいの？ (Shigoto ga isogashii no?)**: 'Are you busy with work?'\n  - **の (no)**: Soft question-ending particle popular in casual speech.\n- **無理しないでね (Muri shinaide ne)**: 'Don't overdo it / Don't push yourself.'\n  - **しないで (shinaide)**: Casual negative request ('don't do [X]').\n\n### 📖 Vocabulary & Readings\n1. **大丈夫 (だいじょうぶ - Daijoubu)**: Okay / all right (Na-adj.)\n2. **仕事 (しごと - Shigoto)**: Work / job (n.)\n3. **忙しい (いそがしい - Isogashii)**: Busy (I-adj.)\n4. **無理 (むり - Muri)**: Impossible / strain (Na-adj./n.)\n\n### 📌 Particles Used\n- **が (ga)**: Subject marker.\n- **ね (ne)**: Caring sentence-ending tag particle.\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Casual friendly sympathy. Expresses closeness and warm concern.",
            "choices": [
                {
                    "text": "ありがとう。今日は早く寝るよ。",
                    "en": "Thank you. I'll go to sleep early today.",
                    "next_node": "end_convo"
                }
            ]
        },
        "friend_plan": {
            "ai_reply": "渋谷に新しいカフェができたんだって！そこ行ってみようよ！",
            "ai_yomi": "しぶや に あたらしい かふぇ が できたんだ って！ そこ いって みよう よ！",
            "ai_romaji": "shibuya ni atarashii kafe ga dekitanda tte! soko itte miyou yo!",
            "ai_en": "I heard a new cafe opened in Shibuya! Let's go check it out!",
            "ai_explain": "### 💡 Grammar & Structure\n- **〜できたんだって！ (~dekitanda tte!)**: 'I heard that [X] was made/opened!'\n  - **〜って (~tte)**: Casual quotient particle used to report hearsay ('I heard that...').\n- **行ってみようよ！ (Itte miyou yo!)**: 'Let's go check it out!'\n  - **〜てみる (~te miru)**: Try doing [X]. Conjugated here to volitional 'みよう' (miyou - let's try).\n\n### 📖 Vocabulary & Readings\n1. **渋谷 (しぶや - Shibuya)**: Shibuya (n., famous district in Tokyo).\n2. **新しい (あたらしい - Atarashii)**: New (I-adj.)\n3. **カフェ (Kafe)**: Cafe (n., Katakana)\n4. **行く (いく - Iku)**: Go (v.)\n\n### 📌 Particles Used\n- **に (ni)**: Location of action destination.\n- **が (ga)**: Subject marker.\n- **よ (yo)**: Volitional emphasis particle ('let's go!').\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Energetic casual talk. Suggests high excitement about trends.",
            "choices": [
                {
                    "text": "いいね！楽しみ！",
                    "en": "Sounds good! Looking forward to it!",
                    "next_node": "end_convo"
                }
            ]
        },
        "friend_busy": {
            "ai_reply": "そっか、残念。じゃあまた今度遊ぼうね！お仕事頑張って！",
            "ai_yomi": "そっか、 ざんねん。 じゃあ また こんど あそぼう ね！ おしごと がんばって！",
            "ai_romaji": "sokka, zannen. jaa mata kondo asobou ne! oshigoto ganbatte!",
            "ai_en": "I see, too bad. Well, let's hang out next time! Good luck with your work!",
            "ai_explain": "### 💡 Grammar & Structure\n- **そっか、残念 (Sokka, zannen)**: 'Ah, I see. That's too bad.'\n- **遊ぼうね (Asobou ne)**: 'Let's hang out / play, okay?' Volitional form of 遊ぶ (asobu) + friendly ne.\n- **お仕事頑張って (Oshigoto ganbatte)**: 'Good luck with work!' Polite prefix お- attached to work, and 'ganbatte' which is te-form of ganbaru (to try hard) used as a friendly cheer.\n\n### 📖 Vocabulary & Readings\n1. **残念 (ざんねん - Zannen)**: Regret / too bad (Na-adj./n.)\n2. **今度 (こんど - Kondo)**: Next time (n.)\n3. **頑張る (がんばる - Ganbaru)**: Persist / work hard (v.)\n\n### 📌 Particles Used\n- **ね (ne)**: Confirmation/softener.\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: Friendly casual encouragement. Standard Japanese way of cheering on a busy friend.",
            "choices": [
                {
                    "text": "うん、またね！ありがとう。",
                    "en": "Yeah, see you later! Thanks.",
                    "next_node": "end_convo"
                }
            ]
        },
        "end_convo": {
            "ai_reply": "はーい！じゃあまた連絡するね。バイバイ！",
            "ai_yomi": "はーい！ じゃあ また れんらく する ね。 ばいばい！",
            "ai_romaji": "haai! jaa mata renraku suru ne. baibai!",
            "ai_en": "Okay! I'll contact you again. Bye bye!",
            "ai_explain": "### 💡 Grammar & Structure\n- **連絡するね (Renraku suru ne)**: 'I'll get in touch with you, okay?' (Future tense indicated by dictionary verb form suru).\n- **バイバイ！ (Baibai)**: 'Bye bye!' universally used casual loanword parting.\n\n### 📖 Vocabulary & Readings\n1. **連絡 (れんらく - Renraku)**: Contact / communication (n./v.)\n2. **バイバイ (Baibai)**: Bye bye (n.)\n\n### 📌 Particles Used\n- **ね (ne)**: Sentence-ending softener.\n\n### 🎭 Formality & Nuance\n- **Politeness Level**: 100% casual daily parting. High intimacy tone.",
            "choices": []
        }
    }
}

# ==================== TOOLTIP COMPONENT ====================
class HoverTooltip:
    def __init__(self, widget, get_text_func):
        self.widget = widget
        self.get_text_func = get_text_func
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
        self.widget.bind("<ButtonPress>", self.hide_tip)

    def show_tip(self, event=None):
        text = self.get_text_func()
        if not text:
            return
        
        # Calculate coordinate placement
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        
        # Premium Apple Midnight Tooltip border frame
        frame = tk.Frame(tw, bg=BG_INNER, highlightbackground=BORDER_COLOR, highlightcolor=BORDER_COLOR, highlightthickness=1)
        frame.pack()
        
        label = tk.Label(
            frame,
            text=text,
            justify="left",
            background=BG_INNER,
            foreground=FG_LIGHT,
            font=(FONT_FAMILY, 9, "normal"),
            padx=8,
            pady=4
        )
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None


# ==================== MAIN APPLICATION CLASS ====================
class JapaneseLearningApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Nihongo Study Core - Standalone Japanese Academy")
        self.root.geometry("1100x700")
        self.root.configure(bg=BG_DARK)
        
        # Set minimum window dimensions
        self.root.minsize(1000, 650)
        
        # State & Database variables
        self.kanji_db = guardian.load_kanji_data()
        self.config = guardian.load_config()
        self.tracker_data = guardian.load_data()
        
        # Active states
        self.difficulty_level = "N5"
        self.active_kanji = None
        self.api_in_progress = False
        
        self.active_learn_kanji = None
        self.learn_api_in_progress = False
        
        self.chat_history = []
        self.active_scenario = "At a Japanese Restaurant"
        self.chat_api_in_progress = False
        self.active_offline_node = "start"
        self.current_view_key = "dashboard"
        
        # Voice recording and Deep Explanation states
        self.voice_recording_in_progress = False
        self.voice_recording_seconds = 5
        self.explaining_message_ids = set()
        self.message_explanations = {}
        self.expanded_explanations = set()
        
        # Sentence builder active selection
        self.selected_builder_words = []
        self.current_lesson_idx = 0
        
        # SRS Review Active state
        self.srs_queue = []
        self.srs_current_idx = 0
        self.srs_show_details = False
        
        # Main Layout Partitioning
        self.create_layouts()
        self.draw_sidebar()
        
        # Start at Dashboard
        self.switch_view("dashboard")

    # ==================== WINDOW LAYOUT INITIALIZER ====================
    def create_layouts(self):
        """Partitions the window into a left sidebar and right content frame."""
        # Main window container
        self.main_container = tk.Frame(self.root, bg=BG_DARK)
        self.main_container.pack(fill="both", expand=True)
        
        # Sidebar Frame
        self.sidebar_frame = tk.Frame(
            self.main_container,
            bg=BG_CARD,
            width=230,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)
        
        # Main Area Content Frame
        self.content_frame = tk.Frame(self.main_container, bg=BG_DARK, padx=25, pady=20)
        self.content_frame.pack(side="right", fill="both", expand=True)

    # ==================== LEFT SIDEBAR NAVIGATION ====================
    def draw_sidebar(self):
        """Renders the sidebar with dynamic status metrics and navigation buttons."""
        # Top Logo Banner
        logo_lbl = tk.Label(
            self.sidebar_frame,
            text="🎌  NIHONGO CLASSIC",
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 11, "bold"),
            pady=20
        )
        logo_lbl.pack()
        
        # Difficulty Level Segmented Buttons Frame
        diff_frame = tk.Frame(self.sidebar_frame, bg=BG_CARD, pady=5)
        diff_frame.pack(fill="x", padx=10)
        
        self.diff_buttons = {}
        for level in ["N5", "N4", "N3", "N2", "N1"]:
            btn = tk.Button(
                diff_frame,
                text=level,
                bg=BG_INNER if level == self.difficulty_level else BG_CARD,
                fg=ACCENT_CYAN if level == self.difficulty_level else FG_SECONDARY,
                activebackground=HOVER_COLOR,
                activeforeground=FG_LIGHT,
                bd=0,
                padx=6,
                pady=4,
                font=(FONT_FAMILY, 8, "bold"),
                cursor="hand2",
                command=lambda l=level: self.change_difficulty(l)
            )
            btn.pack(side="left", fill="x", expand=True, padx=1)
            self.diff_buttons[level] = btn
            
        # Spacing
        spacing_lbl = tk.Label(self.sidebar_frame, text="", bg=BG_CARD, font=(FONT_FAMILY, 4))
        spacing_lbl.pack()
        
        # Navigation Items list
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("learn_kanji", "🎓  Learn Kanji"),
            ("kanji_explorer", "🎋  Kanji Explorer"),
            ("grammar_hub", "📖  Grammar Hub"),
            ("ai_conversation", "💬  AI Conversation"),
            ("srs_review", "⚡  SRS Review Center")
        ]
        
        for view_key, label_text in nav_items:
            btn = tk.Button(
                self.sidebar_frame,
                text=label_text,
                bg=BG_CARD,
                fg=FG_SECONDARY,
                activebackground=HOVER_COLOR,
                activeforeground=FG_LIGHT,
                bd=0,
                anchor="w",
                padx=20,
                pady=12,
                font=(FONT_FAMILY, 9, "bold"),
                cursor="hand2",
                command=lambda k=view_key: self.switch_view(k)
            )
            btn.pack(fill="x", pady=2)
            self.bind_button_hover(btn, BG_CARD, HOVER_COLOR)
            self.nav_buttons[view_key] = btn
            
        # Add visual divider
        divider = tk.Frame(self.sidebar_frame, bg=BORDER_COLOR, height=1)
        divider.pack(fill="x", padx=15, pady=20)
        
        # Bottom Sidebar stats tracker container
        self.sidebar_stats_frame = tk.Frame(self.sidebar_frame, bg=BG_CARD, padx=20)
        self.sidebar_stats_frame.pack(fill="x", side="bottom", pady=20)
        
        self.lbl_streak_sb = tk.Label(
            self.sidebar_stats_frame,
            text="🔥 0 Day Streak",
            fg=ACCENT_ORANGE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 10, "bold"),
            anchor="w"
        )
        self.lbl_streak_sb.pack(fill="x", pady=2)
        
        self.lbl_reviewed_sb = tk.Label(
            self.sidebar_stats_frame,
            text="🧠 0 Kanji Studied",
            fg=ACCENT_GREEN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 8, "bold"),
            anchor="w"
        )
        self.lbl_reviewed_sb.pack(fill="x", pady=2)
        
        self.lbl_due_sb = tk.Label(
            self.sidebar_stats_frame,
            text="⚡ Reviews Due: 0",
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 8, "bold"),
            anchor="w"
        )
        self.lbl_due_sb.pack(fill="x", pady=2)
        
        self.update_sidebar_stats()

    def update_sidebar_stats(self):
        """Calculates and refreshes the live data badges inside the sidebar."""
        # Calculate studied Kanji
        vocab = self.kanji_db.get("vocab", {})
        studied_count = len(vocab)
        
        # Calculate active streak from tracker
        streak = 0
        try:
            stats = guardian.calculate_stats()
            streak = stats.get("current_streak", 0)
        except Exception:
            pass
            
        # Calculate active due reviews
        due_count = 0
        now = datetime.now()
        for c in vocab.values():
            nxt = c.get("next_review")
            if nxt:
                try:
                    if datetime.fromisoformat(nxt) <= now:
                        due_count += 1
                except Exception:
                    pass
                    
        # Apply labels
        self.lbl_streak_sb.config(text=f"🔥  {streak} DAY STREAK")
        self.lbl_reviewed_sb.config(text=f"🧠  {studied_count} Kanji Studied")
        self.lbl_due_sb.config(text=f"⚡  Reviews Due: {due_count}")
        
        # Add dynamic countdown badge value to sidebar reviews item
        if due_count > 0:
            self.nav_buttons["srs_review"].config(text=f"⚡  SRS Review ({due_count})", fg=ACCENT_CYAN)
        else:
            self.nav_buttons["srs_review"].config(text="⚡  SRS Review Center", fg=FG_SECONDARY)

    # ==================== NAVIGATION CONTROLLER ====================
    def switch_view(self, view_key):
        """Cleans current views and swaps in the targeted modular panel."""
        self.current_view_key = view_key
        # Reset navigation highlights
        for key, btn in self.nav_buttons.items():
            btn.config(bg=BG_CARD, fg=FG_SECONDARY)
            
        # Highlight active navigation
        self.nav_buttons[view_key].config(bg=HOVER_COLOR, fg=FG_LIGHT)
        
        # Clear main content children
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Reload databases for real-time consistency
        self.kanji_db = guardian.load_kanji_data()
        self.tracker_data = guardian.load_data()
        self.update_sidebar_stats()
        
        # Launch corresponding view constructor
        if view_key == "dashboard":
            self.draw_dashboard()
        elif view_key == "learn_kanji":
            self.draw_learn_kanji()
        elif view_key == "kanji_explorer":
            self.draw_kanji_explorer()
        elif view_key == "grammar_hub":
            self.draw_grammar_hub()
        elif view_key == "ai_conversation":
            self.draw_ai_conversation()
        elif view_key == "srs_review":
            self.draw_srs_review()

    # ==================== VIEW 1: DASHBOARD HUB ====================
    def draw_dashboard(self):
        """Renders a beautiful greetings dashboard showing overview stats and studied metrics."""
        # Top Header Greeting
        header = tk.Frame(self.content_frame, bg=BG_DARK)
        header.pack(fill="x", pady=(0, 20))
        
        tk.Label(
            header,
            text="こんにちは, 学習者!",
            fg=ACCENT_CYAN,
            bg=BG_DARK,
            font=(FONT_FAMILY, 20, "bold"),
            anchor="w"
        ).pack(anchor="w")
        
        tk.Label(
            header,
            text="Welcome to your Nihongo Study Core. Monitor stats, explore kanji, and review lessons.",
            fg=FG_SECONDARY,
            bg=BG_DARK,
            font=(FONT_FAMILY, 10),
            anchor="w"
        ).pack(anchor="w", pady=(4, 0))
        
        # Grid Container for Action Tiles
        grid_frame = tk.Frame(self.content_frame, bg=BG_DARK)
        grid_frame.pack(fill="both", expand=True)
        
        # Row 1 Frame
        row1 = tk.Frame(grid_frame, bg=BG_DARK)
        row1.pack(fill="x", pady=8)
        
        # Streak Card (Left Column)
        streak = 0
        try:
            stats = guardian.calculate_stats()
            streak = stats.get("current_streak", 0)
        except Exception:
            pass
            
        card_streak = tk.Frame(
            row1,
            bg=BG_CARD,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            padx=20,
            pady=20
        )
        card_streak.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        tk.Label(
            card_streak,
            text="🔥  CURRENT STREAK",
            fg=ACCENT_ORANGE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        ).pack(anchor="w")
        
        tk.Label(
            card_streak,
            text=f"{streak} Days Active",
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 18, "bold")
        ).pack(anchor="w", pady=6)
        
        tk.Label(
            card_streak,
            text="Commit code, study kanji, and complete habits daily to protect your flame!",
            fg=FG_SECONDARY,
            bg=BG_CARD,
            font=(FONT_FAMILY, 8),
            wraplength=350,
            justify="left"
        ).pack(anchor="w")
        
        # SRS Queue Status Card (Right Column)
        vocab = self.kanji_db.get("vocab", {})
        due_count = 0
        now = datetime.now()
        for c in vocab.values():
            nxt = c.get("next_review")
            if nxt:
                try:
                    if datetime.fromisoformat(nxt) <= now:
                        due_count += 1
                except Exception:
                    pass
                    
        card_srs = tk.Frame(
            row1,
            bg=BG_CARD,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            padx=20,
            pady=20
        )
        card_srs.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        tk.Label(
            card_srs,
            text="⚡  SRS REVIEW QUEUE",
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        ).pack(anchor="w")
        
        tk.Label(
            card_srs,
            text=f"{due_count} Vocabulary Due",
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 18, "bold")
        ).pack(anchor="w", pady=6)
        
        btn_start = tk.Button(
            card_srs,
            text="START REVIEW SESSION",
            bg=ACCENT_CYAN if due_count > 0 else BG_INNER,
            fg=FG_LIGHT,
            activebackground="#147ce5",
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self.switch_view("srs_review"),
            state="normal" if due_count > 0 else "disabled"
        )
        btn_start.pack(anchor="w", pady=4)
        if due_count > 0:
            self.bind_button_hover(btn_start, ACCENT_CYAN, "#147ce5")
            
        # Row 2 Frame
        row2 = tk.Frame(grid_frame, bg=BG_DARK)
        row2.pack(fill="both", expand=True, pady=10)
        
        # Daily Vocabulary Inspiration (Left Column)
        card_inspire = tk.Frame(
            row2,
            bg=BG_CARD,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            padx=20,
            pady=20
        )
        card_inspire.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        tk.Label(
            card_inspire,
            text="💡  DAILY INSPIRATION",
            fg=ACCENT_PURPLE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        ).pack(anchor="w")
        
        # Pick a random studied kanji or fallback
        items = list(vocab.values())
        if items:
            inspire_kanji = random.choice(items)
        else:
            inspire_kanji = {
                "kanji": "日",
                "meaning": "day, sun, Japan",
                "onyomi": "ニチ",
                "kunyomi": "ひ",
                "example_ja": "日本にいきたいです。",
                "example_en": "I want to go to Japan."
            }
            
        lbl_k = tk.Label(
            card_inspire,
            text=inspire_kanji.get("kanji"),
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 36, "bold")
        )
        lbl_k.pack(anchor="w", pady=4)
        
        tk.Label(
            card_inspire,
            text=f"Meaning: {inspire_kanji.get('meaning')}",
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 10, "bold")
        ).pack(anchor="w")
        
        tk.Label(
            card_inspire,
            text=f"On: {inspire_kanji.get('onyomi', '(none)')}   |   Kun: {inspire_kanji.get('kunyomi', '(none)')}",
            fg=FG_SECONDARY,
            bg=BG_CARD,
            font=(FONT_FAMILY, 8, "bold")
        ).pack(anchor="w", pady=2)
        
        tk.Label(
            card_inspire,
            text=f"例句: {inspire_kanji.get('example_ja')}",
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9),
            wraplength=350,
            justify="left"
        ).pack(anchor="w", pady=(8, 2))
        
        # Audio Pronounce
        btn_speak = tk.Button(
            card_inspire,
            text="🔊 PRONOUNCE",
            bg=BG_INNER,
            fg=ACCENT_CYAN,
            activebackground=HOVER_COLOR,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=10,
            pady=4,
            cursor="hand2",
            command=lambda: guardian.speak_japanese_text(inspire_kanji.get("example_ja", inspire_kanji.get("kanji")))
        )
        btn_speak.pack(anchor="w", pady=(6, 0))
        self.bind_button_hover(btn_speak, BG_INNER, HOVER_COLOR)
        
        # Fast Dictionary Quick Lookup Widget (Right Column)
        card_lookup = tk.Frame(
            row2,
            bg=BG_CARD,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            padx=20,
            pady=20
        )
        card_lookup.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        tk.Label(
            card_lookup,
            text="🔍  DICTIONARY SEARCH",
            fg=ACCENT_GREEN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        ).pack(anchor="w")
        
        tk.Label(
            card_lookup,
            text="Quickly search studied vocabulary by character or English meaning:",
            fg=FG_SECONDARY,
            bg=BG_CARD,
            font=(FONT_FAMILY, 8),
            wraplength=350,
            justify="left"
        ).pack(anchor="w", pady=(4, 8))
        
        search_entry = tk.Entry(
            card_lookup,
            bg=BG_INNER,
            fg=FG_LIGHT,
            insertbackground=FG_LIGHT,
            bd=1,
            relief="flat",
            font=(FONT_FAMILY, 9)
        )
        search_entry.pack(fill="x", pady=4)
        
        result_lbl = tk.Label(
            card_lookup,
            text="",
            fg=ACCENT_ORANGE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold"),
            justify="left",
            wraplength=350
        )
        result_lbl.pack(anchor="w", fill="both", expand=True, pady=8)
        
        def run_search(e=None):
            q = search_entry.get().strip().lower()
            if not q:
                result_lbl.config(text="")
                return
            for key, val in vocab.items():
                if q in key or q in val.get("meaning", "").lower():
                    result_lbl.config(
                        text=f"Matched: {key} ({val.get('meaning')})\n"
                             f"On: {val.get('onyomi')} | Kun: {val.get('kunyomi')}\n"
                             f"Example: {val.get('example_ja')}"
                    )
                    return
            result_lbl.config(text="No studied Kanji matching query.")
            
        search_entry.bind("<KeyRelease>", run_search)

    # ==================== VIEW 2: KANJI EXPLORER ====================
    def draw_kanji_explorer(self):
        """Displays a dual-panel list/grid layout of Kanji with dynamic Gemini example generator and manual input additions."""
        # Top Header
        header = tk.Frame(self.content_frame, bg=BG_DARK)
        header.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            header,
            text="🎋  KANJI EXPLORER CORE",
            fg=ACCENT_CYAN,
            bg=BG_DARK,
            font=(FONT_FAMILY, 16, "bold")
        ).pack(side="left")
        
        # Dual main columns partition
        explorer_body = tk.Frame(self.content_frame, bg=BG_DARK)
        explorer_body.pack(fill="both", expand=True)
        
        # 1. Left List panel
        list_panel = tk.Frame(explorer_body, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, width=340)
        list_panel.pack(side="left", fill="both")
        list_panel.pack_propagate(False)
        
        # List Panel Search Filter
        search_frame = tk.Frame(list_panel, bg=BG_CARD, padx=10, pady=10)
        search_frame.pack(fill="x")
        
        search_input = tk.Entry(
            search_frame,
            bg=BG_INNER,
            fg=FG_LIGHT,
            insertbackground=FG_LIGHT,
            bd=0,
            font=(FONT_FAMILY, 9)
        )
        search_input.pack(fill="x", pady=(0, 8))
        
        # Filter Buttons frame
        filter_frame = tk.Frame(search_frame, bg=BG_CARD)
        filter_frame.pack(fill="x")
        
        filter_state = tk.StringVar(value="all")
        
        # Kanji Scrollable Container list
        scroll_container = tk.Frame(list_panel, bg=BG_CARD)
        scroll_container.pack(fill="both", expand=True, padx=5, pady=(0, 10))
        
        list_canvas = tk.Canvas(scroll_container, bg=BG_CARD, highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_container, orient="vertical", command=list_canvas.yview)
        list_frame = tk.Frame(list_canvas, bg=BG_CARD)
        
        list_frame.bind(
            "<Configure>",
            lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all"))
        )
        list_canvas.create_window((0, 0), window=list_frame, anchor="nw", width=310)
        list_canvas.configure(yscrollcommand=scrollbar.set)
        
        list_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Capture mouse scroll recursively
        def _on_list_scroll(event):
            if event.delta:
                list_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        list_canvas.bind("<MouseWheel>", _on_list_scroll)
        
        # 2. Right Detail panel
        detail_panel = tk.Frame(explorer_body, bg=BG_DARK, padx=15)
        detail_panel.pack(side="right", fill="both", expand=True)
        
        # Constructor for detail sub-elements inside right panel
        self.detail_body_frame = tk.Frame(detail_panel, bg=BG_DARK)
        self.detail_body_frame.pack(fill="both", expand=True)
        
        def render_explorer_list(e=None):
            # Clear old items
            for child in list_frame.winfo_children():
                child.destroy()
                
            query = search_input.get().strip().lower()
            vocab = self.kanji_db.get("vocab", {})
            
            # Sort items alphabetically by Kanji
            sorted_items = sorted(vocab.values(), key=lambda x: x.get("kanji", ""))
            
            idx = 0
            for item in sorted_items:
                kanji = item.get("kanji")
                meaning = item.get("meaning", "")
                
                # Apply filter
                if query and (query not in kanji and query not in meaning.lower()):
                    continue
                    
                # Highlight if selected
                active_kanji = self.active_kanji.get("kanji") if self.active_kanji else None
                bg_c = HOVER_COLOR if active_kanji == kanji else BG_CARD
                border_c = ACCENT_CYAN if active_kanji == kanji else BORDER_COLOR
                
                row_card = tk.Frame(
                    list_frame,
                    bg=bg_c,
                    pady=8,
                    padx=12,
                    highlightbackground=border_c,
                    highlightthickness=1,
                    cursor="hand2"
                )
                row_card.pack(fill="x", pady=3)
                
                k_lbl = tk.Label(row_card, text=kanji, fg=ACCENT_CYAN, bg=bg_c, font=(FONT_FAMILY, 14, "bold"))
                k_lbl.pack(side="left", padx=5)
                
                m_lbl = tk.Label(row_card, text=meaning[:20] + ("..." if len(meaning) > 20 else ""), fg=FG_LIGHT, bg=bg_c, font=(FONT_FAMILY, 8, "bold"))
                m_lbl.pack(side="left", padx=10)
                
                srs = item.get("srs_stage", 1)
                srs_lbl = tk.Label(row_card, text=f"SRS: {srs}", fg=ACCENT_ORANGE, bg=bg_c, font=(FONT_FAMILY, 7, "bold"))
                srs_lbl.pack(side="right", padx=5)
                
                # Bind select commands
                def bind_select_card(w, target_item=item):
                    def action(e):
                        self.active_kanji = target_item
                        self.render_kanji_details_pane()
                        render_explorer_list()
                    w.bind("<Button-1>", action)
                    for c in w.winfo_children():
                        c.bind("<Button-1>", action)
                        
                bind_select_card(row_card)
                self.bind_hover_highlight(row_card, bg_c, HOVER_COLOR)
                
                # Capture scroll
                row_card.bind("<MouseWheel>", _on_list_scroll)
                for child in row_card.winfo_children():
                    child.bind("<MouseWheel>", _on_list_scroll)
                    
            # Draw standard Manual Custom creation button at bottom of list
            btn_add_kanji = tk.Button(
                list_frame,
                text="➕  ADD CUSTOM KANJI",
                bg=BG_INNER,
                fg=ACCENT_CYAN,
                activebackground=HOVER_COLOR,
                activeforeground=FG_LIGHT,
                bd=0,
                font=(FONT_FAMILY, 8, "bold"),
                pady=10,
                cursor="hand2",
                command=self.open_custom_kanji_form
            )
            btn_add_kanji.pack(fill="x", pady=10)
            self.bind_button_hover(btn_add_kanji, BG_INNER, HOVER_COLOR)
            
        search_input.bind("<KeyRelease>", render_explorer_list)
        
        # Load first studied card as active card if available
        vocab_pool = list(self.kanji_db.get("vocab", {}).values())
        if vocab_pool and not self.active_kanji:
            self.active_kanji = sorted(vocab_pool, key=lambda x: x.get("kanji", ""))[0]
            
        render_explorer_list()
        self.render_kanji_details_pane()

    def render_kanji_details_pane(self):
        """Builds the rich detailed visualization for the active Kanji card in the right Explorer panel."""
        # Clear right main detail container
        for child in self.detail_body_frame.winfo_children():
            child.destroy()
            
        if not self.active_kanji:
            no_card = tk.Frame(self.detail_body_frame, bg=BG_DARK, pady=100)
            no_card.pack(fill="both", expand=True)
            tk.Label(
                no_card,
                text="🎋 No Kanji Selected",
                fg=FG_SECONDARY,
                bg=BG_DARK,
                font=(FONT_FAMILY, 14, "bold")
            ).pack()
            tk.Label(
                no_card,
                text="Select a studied Kanji from the left list or add a custom card to view details.",
                fg=FG_SECONDARY,
                bg=BG_DARK,
                font=(FONT_FAMILY, 9)
            ).pack(pady=4)
            return
            
        item = self.active_kanji
        
        # Header Row Details card
        card_frame = tk.Frame(
            self.detail_body_frame,
            bg=BG_CARD,
            padx=25,
            pady=25,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        card_frame.pack(fill="both", expand=True)
        
        # Big Kanji character display
        left_header = tk.Frame(card_frame, bg=BG_CARD)
        left_header.pack(fill="x")
        
        kanji_lbl = tk.Label(
            left_header,
            text=item.get("kanji"),
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 64, "bold"),
            cursor="hand2"
        )
        kanji_lbl.pack(side="left", padx=(0, 20))
        HoverTooltip(kanji_lbl, lambda: item.get("kanji_romaji", ""))
        
        details_col = tk.Frame(left_header, bg=BG_CARD)
        details_col.pack(side="left", fill="y", pady=10)
        
        meaning_lbl = tk.Label(
            details_col,
            text=item.get("meaning", "").upper(),
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 16, "bold"),
            justify="left"
        )
        meaning_lbl.pack(anchor="w")
        
        yomi_lbl = tk.Label(
            details_col,
            text=f"読み: {item.get('kanji_yomi', '')}",
            fg=FG_SECONDARY,
            bg=BG_CARD,
            font=(FONT_FAMILY, 11, "bold")
        )
        yomi_lbl.pack(anchor="w", pady=2)
        HoverTooltip(yomi_lbl, lambda: item.get("kanji_romaji", ""))
        
        # Row 2: Readings Details
        readings_frame = tk.Frame(card_frame, bg=BG_INNER, padx=15, pady=12, highlightbackground=BORDER_COLOR, highlightthickness=1)
        readings_frame.pack(fill="x", pady=15)
        
        onyomi = item.get("onyomi", "")
        onyomi_txt = f"音読み (Onyomi): {onyomi}" if onyomi else "音読み (Onyomi): (none)"
        lbl_on = tk.Label(readings_frame, text=onyomi_txt, fg=ACCENT_ORANGE, bg=BG_INNER, font=(FONT_FAMILY, 9, "bold"))
        lbl_on.pack(anchor="w")
        HoverTooltip(lbl_on, lambda: item.get("kanji_romaji", ""))
        
        kunyomi = item.get("kunyomi", "")
        kunyomi_txt = f"訓読み (Kunyomi): {kunyomi}" if kunyomi else "訓読み (Kunyomi): (none)"
        lbl_kun = tk.Label(readings_frame, text=kunyomi_txt, fg=ACCENT_GREEN, bg=BG_INNER, font=(FONT_FAMILY, 9, "bold"))
        lbl_kun.pack(anchor="w", pady=(4, 0))
        HoverTooltip(lbl_kun, lambda: item.get("kanji_romaji", ""))
        
        # Row 3: Example Sentence Details
        example_frame = tk.Frame(card_frame, bg=BG_CARD)
        example_frame.pack(fill="x", pady=10)
        
        tk.Label(
            example_frame,
            text="例句 (EXAMPLE SENTENCE)",
            fg=ACCENT_PURPLE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        ).pack(anchor="w")
        
        # The sentence content card
        sentence_box = tk.Frame(example_frame, bg=BG_INNER, padx=15, pady=15, highlightbackground=BORDER_COLOR, highlightthickness=1)
        sentence_box.pack(fill="x", pady=6)
        
        lbl_sentence_ja = tk.Label(
            sentence_box,
            text=item.get("example_ja"),
            fg=FG_LIGHT,
            bg=BG_INNER,
            font=(FONT_FAMILY, 12),
            wraplength=450,
            justify="left"
        )
        lbl_sentence_ja.pack(anchor="w")
        HoverTooltip(lbl_sentence_ja, lambda: item.get("example_romaji", ""))
        
        lbl_sentence_en = tk.Label(
            sentence_box,
            text=item.get("example_en"),
            fg=FG_SECONDARY,
            bg=BG_INNER,
            font=(FONT_FAMILY, 9, "italic"),
            wraplength=450,
            justify="left"
        )
        lbl_sentence_en.pack(anchor="w", pady=(4, 0))
        
        # Action Row Buttons inside Details card
        action_row = tk.Frame(card_frame, bg=BG_CARD)
        action_row.pack(fill="x", side="bottom", pady=(10, 0))
        
        # 1. Sound plays text pronunciation natively
        btn_pron_k = tk.Button(
            action_row,
            text="🔊 PRONOUNCE KANJI",
            bg=BG_INNER,
            fg=ACCENT_CYAN,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=12,
            pady=8,
            cursor="hand2",
            command=lambda: guardian.speak_japanese_text(item.get("kanji_yomi", item.get("kanji")))
        )
        btn_pron_k.pack(side="left", padx=2)
        self.bind_button_hover(btn_pron_k, BG_INNER, HOVER_COLOR)
        
        btn_pron_s = tk.Button(
            action_row,
            text="🔊 PRONOUNCE SENTENCE",
            bg=BG_INNER,
            fg=ACCENT_CYAN,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=12,
            pady=8,
            cursor="hand2",
            command=lambda: guardian.speak_japanese_text(item.get("example_ja"))
        )
        btn_pron_s.pack(side="left", padx=2)
        self.bind_button_hover(btn_pron_s, BG_INNER, HOVER_COLOR)
        
        # 2. Gemini sentence refresher helper
        btn_refresh = tk.Button(
            action_row,
            text="↻  REFRESH SENTENCE",
            bg=BG_INNER,
            fg=ACCENT_ORANGE,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=12,
            pady=8,
            cursor="hand2",
            command=self.refresh_explorer_example_sentence
        )
        btn_refresh.pack(side="right", padx=2)
        self.bind_button_hover(btn_refresh, BG_INNER, HOVER_COLOR)

    def refresh_explorer_example_sentence(self):
        """Async triggers Gemini API call to generate a fresh, new Japanese sentence for current Kanji."""
        if not self.active_kanji or self.api_in_progress:
            return
            
        kanji = self.active_kanji.get("kanji")
        self.api_in_progress = True
        
        def run_refresh():
            api_key = self.config.get("gemini_api_key", "").strip()
            new_res = guardian.get_gemini_example_sentence(api_key, kanji)
            self.root.after(0, lambda: self.on_refresh_sentence_resolved(new_res))
            
        threading.Thread(target=run_refresh, daemon=True).start()

    def on_refresh_sentence_resolved(self, new_sentence):
        self.api_in_progress = False
        if not new_sentence or not self.active_kanji:
            return
            
        kanji_key = self.active_kanji.get("kanji")
        vocab = self.kanji_db.get("vocab", {})
        
        if kanji_key in vocab:
            vocab[kanji_key]["example_ja"] = new_sentence.get("example_ja", "")
            vocab[kanji_key]["example_en"] = new_sentence.get("example_en", "")
            vocab[kanji_key]["example_yomi"] = new_sentence.get("example_yomi", "")
            vocab[kanji_key]["example_romaji"] = new_sentence.get("example_romaji", "")
            
            # Save and update active card frame
            self.active_kanji = vocab[kanji_key]
            guardian.save_kanji_data(self.kanji_db)
            self.render_kanji_details_pane()

    def open_custom_kanji_form(self):
        """Launches a modal top dialog form allowing manual input/creation of custom Kanji cards."""
        modal = tk.Toplevel(self.root)
        modal.title("➕ Create Custom Kanji Vocabulary")
        modal.configure(bg=BG_DARK)
        modal.geometry("380x560")
        modal.resizable(False, False)
        modal.attributes("-topmost", True)
        
        # Center relative to root window
        mx = self.root.winfo_x() + 300
        my = self.root.winfo_y() + 80
        modal.geometry(f"+{mx}+{my}")
        
        # Title Header
        tk.Label(
            modal,
            text="➕  ADD CUSTOM KANJI NODE",
            fg=ACCENT_CYAN,
            bg=BG_DARK,
            font=(FONT_FAMILY, 11, "bold"),
            pady=15
        ).pack()
        
        form_frame = tk.Frame(modal, bg=BG_DARK, padx=20)
        form_frame.pack(fill="both", expand=True)
        
        # Custom Form Entries
        fields = [
            ("kanji", "Kanji Character (e.g. 木):"),
            ("meaning", "English Meaning (e.g. tree, wood):"),
            ("yomi", "Hiragana Reading (e.g. き):"),
            ("romaji", "Romaji Reading (e.g. ki):"),
            ("onyomi", "Onyomi (Chinese reading - e.g. モク):"),
            ("kunyomi", "Kunyomi (Japanese reading - e.g. き):"),
            ("ex_ja", "Example Japanese Sentence:"),
            ("ex_en", "Example English Translation:")
        ]
        
        entries = {}
        for key, prompt in fields:
            tk.Label(form_frame, text=prompt, fg=FG_LIGHT, bg=BG_DARK, font=(FONT_FAMILY, 8, "bold")).pack(anchor="w", pady=(4, 1))
            entry = tk.Entry(form_frame, bg=BG_CARD, fg=FG_LIGHT, insertbackground=FG_LIGHT, bd=1, relief="flat", font=(FONT_FAMILY, 9))
            entry.pack(fill="x")
            entries[key] = entry
            
        def submit_custom_card():
            k = entries["kanji"].get().strip()
            meaning = entries["meaning"].get().strip()
            yomi = entries["yomi"].get().strip()
            romaji = entries["romaji"].get().strip()
            onyomi = entries["onyomi"].get().strip()
            kunyomi = entries["kunyomi"].get().strip()
            ex_ja = entries["ex_ja"].get().strip()
            ex_en = entries["ex_en"].get().strip()
            
            if not k or not meaning or not yomi or not romaji or not ex_ja or not ex_en:
                messagebox.showerror("Validation Error", "All fields except Onyomi and Kunyomi are required!", parent=modal)
                return
                
            vocab = self.kanji_db.setdefault("vocab", {})
            if k in vocab:
                messagebox.showerror("Conflict Warning", f"Kanji '{k}' is already studied in your database!", parent=modal)
                return
                
            vocab[k] = {
                "kanji": k,
                "meaning": meaning,
                "onyomi": onyomi,
                "kunyomi": kunyomi,
                "stroke_count": len(k),
                "example_ja": ex_ja,
                "example_en": ex_en,
                "kanji_yomi": yomi,
                "kanji_romaji": romaji,
                "example_yomi": yomi,
                "example_romaji": romaji,
                "level": "Custom",
                "srs_stage": 1,
                "next_review": (datetime.now() + timedelta(days=1)).isoformat(),
                "history": []
            }
            
            guardian.save_kanji_data(self.kanji_db)
            modal.destroy()
            
            # Reset active card and redraw panel
            self.active_kanji = vocab[k]
            self.switch_view("kanji_explorer")
            messagebox.showinfo("Success", f"Custom Kanji '{k}' added successfully!", parent=self.root)
            
        btn_submit = tk.Button(
            modal,
            text="SAVE CUSTOM KANJI",
            bg=ACCENT_CYAN,
            fg=FG_LIGHT,
            activebackground="#147ce5",
            bd=0,
            font=(FONT_FAMILY, 9, "bold"),
            pady=10,
            cursor="hand2",
            command=submit_custom_card
        )
        btn_submit.pack(fill="x", side="bottom", padx=20, pady=15)
        self.bind_button_hover(btn_submit, ACCENT_CYAN, "#147ce5")

    # ==================== VIEW 3: GRAMMAR HUB ====================
    def draw_grammar_hub(self):
        """Renders the modular categorized Japanese grammar lesson lists."""
        # Top Header
        header = tk.Frame(self.content_frame, bg=BG_DARK)
        header.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            header,
            text="📖  GRAMMAR HUB & ACADEMY",
            fg=ACCENT_CYAN,
            bg=BG_DARK,
            font=(FONT_FAMILY, 16, "bold")
        ).pack(side="left")
        
        # Grid Container for Lesson lists
        scroll_frame = tk.Frame(self.content_frame, bg=BG_DARK)
        scroll_frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(scroll_frame, bg=BG_DARK, highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        lessons_grid = tk.Frame(canvas, bg=BG_DARK)
        
        lessons_grid.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=lessons_grid, anchor="nw", width=800)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Capture mouse scroll recursively
        def _on_grid_scroll(event):
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _on_grid_scroll)
        
        # Retrieve lesson progress database
        progress = self.kanji_db.setdefault("grammar_progress", {})
        
        # Build cards for each lesson
        active_lessons = JLPT_GRAMMAR_LESSONS.get(self.difficulty_level, GRAMMAR_LESSONS)
        idx = 1
        for lesson in active_lessons:
            lesson_id = lesson.get("id")
            is_learned = progress.get(lesson_id, False)
            
            # Glowing border highlight if complete
            border_color = ACCENT_GREEN if is_learned else BORDER_COLOR
            card = tk.Frame(
                lessons_grid,
                bg=BG_CARD,
                pady=15,
                padx=20,
                highlightbackground=border_color,
                highlightthickness=1
            )
            card.pack(fill="x", pady=6)
            
            # Header Row
            row_title = tk.Frame(card, bg=BG_CARD)
            row_title.pack(fill="x")
            
            title_text = f"✓  {lesson.get('title')}" if is_learned else lesson.get("title")
            title_color = ACCENT_GREEN if is_learned else FG_LIGHT
            tk.Label(
                row_title,
                text=title_text,
                fg=title_color,
                bg=BG_CARD,
                font=(FONT_FAMILY, 10, "bold")
            ).pack(side="left")
            
            # Short Desc
            tk.Label(
                card,
                text=lesson.get("desc"),
                fg=FG_SECONDARY,
                bg=BG_CARD,
                font=(FONT_FAMILY, 8),
                wraplength=700,
                justify="left"
            ).pack(anchor="w", pady=(6, 4))
            
            # Start button
            def bind_start_lesson(target_idx=idx-1):
                return lambda: self.launch_interactive_lesson(target_idx)
                
            btn_start = tk.Button(
                card,
                text="STUDY LESSON",
                bg=BG_INNER,
                fg=ACCENT_CYAN,
                activebackground=HOVER_COLOR,
                bd=0,
                font=(FONT_FAMILY, 8, "bold"),
                padx=10,
                pady=5,
                cursor="hand2",
                command=bind_start_lesson(idx-1)
            )
            btn_start.pack(anchor="w", pady=(6, 0))
            self.bind_button_hover(btn_start, BG_INNER, HOVER_COLOR)
            
            self.bind_hover_highlight(card, BG_CARD, HOVER_COLOR)
            card.bind("<MouseWheel>", _on_grid_scroll)
            for c in card.winfo_children():
                c.bind("<MouseWheel>", _on_grid_scroll)
                
            idx += 1

    def launch_interactive_lesson(self, lesson_idx):
        """Replaces main content view with the interactive detailed Grammar study card."""
        self.current_lesson_idx = lesson_idx
        active_lessons = JLPT_GRAMMAR_LESSONS.get(self.difficulty_level, GRAMMAR_LESSONS)
        lesson = active_lessons[lesson_idx]
        
        # Reset selection order
        self.selected_builder_words = []
        
        # Clear view
        for child in self.content_frame.winfo_children():
            child.destroy()
            
        # Lesson Frame Layout
        container = tk.Frame(self.content_frame, bg=BG_DARK)
        container.pack(fill="both", expand=True)
        
        # 1. Back button row
        back_row = tk.Frame(container, bg=BG_DARK)
        back_row.pack(fill="x", pady=(0, 10))
        
        btn_back = tk.Button(
            back_row,
            text="⬅️  BACK TO GRAMMAR LIST",
            bg=BG_CARD,
            fg=FG_LIGHT,
            activebackground=HOVER_COLOR,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self.switch_view("grammar_hub")
        )
        btn_back.pack(side="left")
        self.bind_button_hover(btn_back, BG_CARD, HOVER_COLOR)
        
        # Main Detail Study Card
        self.lesson_card = tk.Frame(
            container,
            bg=BG_CARD,
            padx=25,
            pady=20,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        self.lesson_card.pack(fill="both", expand=True)
        
        # Lesson Title
        tk.Label(
            self.lesson_card,
            text=lesson.get("title"),
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 16, "bold")
        ).pack(anchor="w")
        
        tk.Label(
            self.lesson_card,
            text=lesson.get("desc"),
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 10),
            wraplength=750,
            justify="left"
        ).pack(anchor="w", pady=(8, 12))
        
        # Concept Formula Frame
        formula_box = tk.Frame(self.lesson_card, bg=BG_INNER, padx=15, pady=12, highlightbackground=BORDER_COLOR, highlightthickness=1)
        formula_box.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            formula_box,
            text="GRAMMATICAL CONCEPT",
            fg=ACCENT_ORANGE,
            bg=BG_INNER,
            font=(FONT_FAMILY, 8, "bold")
        ).pack(anchor="w")
        
        tk.Label(
            formula_box,
            text=lesson.get("concept"),
            fg=FG_LIGHT,
            bg=BG_INNER,
            font=(FONT_FAMILY, 10, "bold"),
            justify="left"
        ).pack(anchor="w", pady=(4, 0))
        
        # Interactive Sentence Builder Panel
        self.sentence_builder_frame = tk.Frame(self.lesson_card, bg=BG_CARD)
        self.sentence_builder_frame.pack(fill="x", pady=10)
        
        self.render_sentence_builder_game()
        
        # Persistent learning completion
        bottom_row = tk.Frame(self.lesson_card, bg=BG_CARD)
        bottom_row.pack(fill="x", side="bottom", pady=(15, 0))
        
        progress = self.kanji_db.get("grammar_progress", {})
        is_learned = progress.get(lesson.get("id"), False)
        
        def mark_lesson_complete():
            l_id = lesson.get("id")
            progress[l_id] = not progress.get(l_id, False)
            guardian.save_kanji_data(self.kanji_db)
            self.launch_interactive_lesson(lesson_idx)
            
        btn_mark = tk.Button(
            bottom_row,
            text="✓  MARK LESSON COMPLETE" if not is_learned else "✓  UNMARK COMPLETION",
            bg=ACCENT_GREEN if is_learned else ACCENT_CYAN,
            fg=FG_LIGHT,
            activebackground="#147ce5",
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=12,
            pady=8,
            cursor="hand2",
            command=mark_lesson_complete
        )
        btn_mark.pack(side="left")
        self.bind_button_hover(btn_mark, ACCENT_GREEN if is_learned else ACCENT_CYAN, "#147ce5")

    def render_sentence_builder_game(self):
        """Constructs the interactive drag/click particle slots game inside grammar lessons."""
        # Clear builder subframe
        for child in self.sentence_builder_frame.winfo_children():
            child.destroy()
            
        active_lessons = JLPT_GRAMMAR_LESSONS.get(self.difficulty_level, GRAMMAR_LESSONS)
        lesson = active_lessons[self.current_lesson_idx]
        builder = lesson.get("builder")
        
        tk.Label(
            self.sentence_builder_frame,
            text="⚡  INTERACTIVE SENTENCE BUILDER GAME",
            fg=ACCENT_PURPLE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        ).pack(anchor="w")
        
        tk.Label(
            self.sentence_builder_frame,
            text=f"Translate this sentence to Japanese: '{builder.get('english')}'",
            fg=FG_SECONDARY,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9)
        ).pack(anchor="w", pady=(2, 8))
        
        # 1. Selection slots display frame (Empty or filled slots)
        slots_panel = tk.Frame(
            self.sentence_builder_frame,
            bg=BG_INNER,
            pady=15,
            padx=15,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        slots_panel.pack(fill="x", pady=6)
        
        # Populate selected word badges
        if not self.selected_builder_words:
            lbl_tip = tk.Label(slots_panel, text="Click on the word pill blocks below in correct order...", fg=FG_SECONDARY, bg=BG_INNER, font=(FONT_FAMILY, 9, "italic"))
            lbl_tip.pack()
        else:
            for word in self.selected_builder_words:
                badge = tk.Label(
                    slots_panel,
                    text=word,
                    bg=BG_DARK,
                    fg=ACCENT_CYAN,
                    font=(FONT_FAMILY, 10, "bold"),
                    padx=10,
                    pady=4,
                    relief="flat"
                )
                badge.pack(side="left", padx=3)
                
        # 2. Tray frame containing available word pills
        tray_panel = tk.Frame(self.sentence_builder_frame, bg=BG_CARD, pady=10)
        tray_panel.pack(fill="x")
        
        for option in builder.get("options"):
            # If word is already selected, disable or skip showing
            times_selected = self.selected_builder_words.count(option)
            times_total = builder.get("options").count(option)
            
            # Basic validation
            state_val = "normal"
            bg_c = BG_INNER
            fg_c = FG_LIGHT
            if times_selected >= times_total:
                state_val = "disabled"
                bg_c = BG_CARD
                fg_c = FG_SECONDARY
                
            def make_click_cmd(w=option):
                return lambda: self.select_builder_word(w)
                
            pill = tk.Button(
                tray_panel,
                text=option,
                bg=bg_c,
                fg=fg_c,
                activebackground=HOVER_COLOR,
                activeforeground=FG_LIGHT,
                bd=0,
                font=(FONT_FAMILY, 9, "bold"),
                padx=12,
                pady=6,
                state=state_val,
                cursor="hand2" if state_val == "normal" else "arrow",
                command=make_click_cmd(option)
            )
            pill.pack(side="left", padx=4)
            if state_val == "normal":
                self.bind_button_hover(pill, bg_c, HOVER_COLOR)
                
        # Reset and Check Action controls
        ctrls = tk.Frame(self.sentence_builder_frame, bg=BG_CARD)
        ctrls.pack(fill="x", pady=(5, 0))
        
        btn_reset = tk.Button(
            ctrls,
            text="↻  RESET GAME",
            bg=BG_INNER,
            fg=ACCENT_RED,
            activebackground=HOVER_COLOR,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.reset_builder_game
        )
        btn_reset.pack(side="left", padx=2)
        self.bind_button_hover(btn_reset, BG_INNER, HOVER_COLOR)
        
        btn_check = tk.Button(
            ctrls,
            text="⚡  EVALUATE SENTENCE",
            bg=ACCENT_CYAN,
            fg=FG_LIGHT,
            activebackground="#147ce5",
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=12,
            pady=5,
            cursor="hand2",
            command=self.check_sentence_builder_correctness
        )
        btn_check.pack(side="left", padx=10)
        self.bind_button_hover(btn_check, ACCENT_CYAN, "#147ce5")

    def select_builder_word(self, word):
        """Triggered when user clicks a tray word pill block."""
        self.selected_builder_words.append(word)
        self.render_sentence_builder_game()

    def reset_builder_game(self):
        """Cleans selected word sequence and redraws game board."""
        self.selected_builder_words = []
        self.render_sentence_builder_game()
        # Reset card outlines
        self.lesson_card.config(highlightbackground=BORDER_COLOR)

    def check_sentence_builder_correctness(self):
        """Validates if selected words match the correct grammatical sentence sequence."""
        active_lessons = JLPT_GRAMMAR_LESSONS.get(self.difficulty_level, GRAMMAR_LESSONS)
        lesson = active_lessons[self.current_lesson_idx]
        builder = lesson.get("builder")
        correct = builder.get("correct_order")
        
        if self.selected_builder_words == correct:
            # Speak Correct response out loud
            guardian.speak_japanese_text("せいかい！ 正解")
            
            # Glowing Green Aura flash highlight success
            self.lesson_card.config(highlightbackground=ACCENT_GREEN, highlightthickness=1)
            messagebox.showinfo("🎉 EXCELLENT!", "Correct sequence built! You have successfully mastered this sentence structure!", parent=self.root)
        else:
            # Speak Mistake response
            guardian.speak_japanese_text("まちがい！ 間違い")
            
            # Glowing Red Aura highlight error
            self.lesson_card.config(highlightbackground=ACCENT_RED, highlightthickness=1)
            messagebox.showerror("❌ MISTAKE", "Ah, that is not quite right! Keep trying and check the grammatical concept above.", parent=self.root)

    # ==================== VIEW 4: SRS REVIEW CENTER ====================
    def draw_srs_review(self):
        """Builds the active SRS card reviewing terminal panel."""
        # Top Header
        header = tk.Frame(self.content_frame, bg=BG_DARK)
        header.pack(fill="x", pady=(0, 20))
        
        tk.Label(
            header,
            text="⚡  SRS REVIEW CENTER",
            fg=ACCENT_CYAN,
            bg=BG_DARK,
            font=(FONT_FAMILY, 16, "bold")
        ).pack(side="left")
        
        # Main body study frame
        self.srs_body_frame = tk.Frame(self.content_frame, bg=BG_DARK)
        self.srs_body_frame.pack(fill="both", expand=True)
        
        # Scan studied nodes for due reviews
        vocab = self.kanji_db.get("vocab", {})
        now = datetime.now()
        
        self.srs_queue = []
        for c in vocab.values():
            nxt = c.get("next_review")
            if nxt:
                try:
                    if datetime.fromisoformat(nxt) <= now:
                        self.srs_queue.append(c)
                except Exception:
                    pass
                    
        # Shuffle review queue for maximum active learning randomized triggers
        random.shuffle(self.srs_queue)
        
        self.srs_current_idx = 0
        self.srs_show_details = False
        self.render_srs_flashcard_state()

    def render_srs_flashcard_state(self):
        """Draws the selected active flashcard in due reviews or final Inbox Zero card."""
        # Clear body frame
        for child in self.srs_body_frame.winfo_children():
            child.destroy()
            
        # 1. Caught up (Inbox Zero)
        if not self.srs_queue or self.srs_current_idx >= len(self.srs_queue):
            inbox_zero = tk.Frame(
                self.srs_body_frame,
                bg=BG_CARD,
                padx=35,
                pady=40,
                highlightbackground=BORDER_COLOR,
                highlightthickness=1
            )
            inbox_zero.pack(fill="x", pady=50)
            
            tk.Label(
                inbox_zero,
                text="🎉  ALL CAUGHT UP!",
                fg=ACCENT_GREEN,
                bg=BG_CARD,
                font=(FONT_FAMILY, 18, "bold")
            ).pack()
            
            tk.Label(
                inbox_zero,
                text="Outstanding work! Your SRS review queue is completely empty.\n"
                     "Explore studied vocabulary or add new manual custom cards to schedule more items.",
                fg=FG_LIGHT,
                bg=BG_CARD,
                font=(FONT_FAMILY, 10),
                pady=15,
                justify="center"
            ).pack()
            
            # Simple button returning to explorer
            btn_go = tk.Button(
                inbox_zero,
                text="EXPLORE KANJI DATABASE",
                bg=ACCENT_CYAN,
                fg=FG_LIGHT,
                activebackground="#147ce5",
                bd=0,
                font=(FONT_FAMILY, 8, "bold"),
                padx=15,
                pady=8,
                cursor="hand2",
                command=lambda: self.switch_view("kanji_explorer")
            )
            btn_go.pack()
            self.bind_button_hover(btn_go, ACCENT_CYAN, "#147ce5")
            return
            
        # 2. Reviews due
        card_data = self.srs_queue[self.srs_current_idx]
        
        # Central card review container
        card_container = tk.Frame(
            self.srs_body_frame,
            bg=BG_CARD,
            padx=35,
            pady=30,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        card_container.pack(fill="both", expand=True)
        
        # Queue count index header
        tk.Label(
            card_container,
            text=f"REVIEWING ITEM: {self.srs_current_idx + 1} OF {len(self.srs_queue)}",
            fg=ACCENT_ORANGE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 8, "bold")
        ).pack(anchor="w")
        
        # Large Kanji visual display
        kanji_lbl = tk.Label(
            card_container,
            text=card_data.get("kanji"),
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 72, "bold"),
            cursor="hand2"
        )
        kanji_lbl.pack(pady=10)
        HoverTooltip(kanji_lbl, lambda: card_data.get("kanji_romaji", ""))
        
        # Windowless speech triggers on sound
        btn_speak = tk.Button(
            card_container,
            text="🔊 PRONOUNCE KANJI",
            bg=BG_INNER,
            fg=ACCENT_CYAN,
            activebackground=HOVER_COLOR,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=10,
            pady=4,
            cursor="hand2",
            command=lambda: guardian.speak_japanese_text(card_data.get("kanji_yomi", card_data.get("kanji")))
        )
        btn_speak.pack(pady=(0, 15))
        self.bind_button_hover(btn_speak, BG_INNER, HOVER_COLOR)
        
        # If card is hidden, show single click action button to slide details
        if not self.srs_show_details:
            btn_show = tk.Button(
                card_container,
                text="🔍  SHOW MEANING & READINGS",
                bg=ACCENT_CYAN,
                fg=FG_LIGHT,
                activebackground="#147ce5",
                bd=0,
                font=(FONT_FAMILY, 10, "bold"),
                padx=20,
                pady=10,
                cursor="hand2",
                command=self.show_srs_card_details
            )
            btn_show.pack(pady=20)
            self.bind_button_hover(btn_show, ACCENT_CYAN, "#147ce5")
        else:
            # Show all hidden card metrics
            info_frame = tk.Frame(card_container, bg=BG_INNER, padx=20, pady=15, highlightbackground=BORDER_COLOR, highlightthickness=1)
            info_frame.pack(fill="x", pady=10)
            
            lbl_m = tk.Label(
                info_frame,
                text=f"Meaning: {card_data.get('meaning')}".upper(),
                fg=BG_INNER,
                bg=BG_INNER,
                font=(FONT_FAMILY, 11, "bold")
            )
            lbl_m.pack(anchor="w")
            
            lbl_o = tk.Label(
                info_frame,
                text=f"Onyomi (音): {card_data.get('onyomi', '(none)')}      Kunyomi (訓): {card_data.get('kunyomi', '(none)')}",
                fg=BG_INNER,
                bg=BG_INNER,
                font=(FONT_FAMILY, 9, "bold")
            )
            lbl_o.pack(anchor="w", pady=(4, 0))
            
            widgets_to_fade = [
                (lbl_m, FG_LIGHT),
                (lbl_o, FG_SECONDARY)
            ]
            
            # Show example sentences
            ex_ja = card_data.get("example_ja")
            if ex_ja:
                lbl_e_ja = tk.Label(
                    info_frame,
                    text=f"例句: {ex_ja}",
                    fg=BG_INNER,
                    bg=BG_INNER,
                    font=(FONT_FAMILY, 9),
                    wraplength=600,
                    justify="left"
                )
                lbl_e_ja.pack(anchor="w", pady=(10, 2))
                HoverTooltip(lbl_e_ja, lambda: card_data.get("example_romaji", ""))
                
                lbl_e_en = tk.Label(
                    info_frame,
                    text=card_data.get("example_en"),
                    fg=BG_INNER,
                    bg=BG_INNER,
                    font=(FONT_FAMILY, 8, "italic"),
                    wraplength=600,
                    justify="left"
                )
                lbl_e_en.pack(anchor="w")
                
                widgets_to_fade.append((lbl_e_ja, FG_LIGHT))
                widgets_to_fade.append((lbl_e_en, FG_SECONDARY))
                
            self.animate_text_fade(widgets_to_fade)
                
            # Evaluation control buttons (Correct / Incorrect)
            eval_frame = tk.Frame(card_container, bg=BG_CARD)
            eval_frame.pack(fill="x", side="bottom", pady=(10, 0))
            
            btn_correct = tk.Button(
                eval_frame,
                text="✓  I KNEW IT (CORRECT)",
                bg=ACCENT_GREEN,
                fg=FG_LIGHT,
                activebackground="#2aa848",
                bd=0,
                font=(FONT_FAMILY, 9, "bold"),
                padx=15,
                pady=10,
                cursor="hand2",
                command=lambda: self.submit_srs_evaluation(True)
            )
            btn_correct.pack(side="left", fill="x", expand=True, padx=(0, 4))
            self.bind_button_hover(btn_correct, ACCENT_GREEN, "#2aa848")
            
            btn_wrong = tk.Button(
                eval_frame,
                text="✕  WRONG / MISTAKE",
                bg=ACCENT_RED,
                fg=FG_LIGHT,
                activebackground="#e0372d",
                bd=0,
                font=(FONT_FAMILY, 9, "bold"),
                padx=15,
                pady=10,
                cursor="hand2",
                command=lambda: self.submit_srs_evaluation(False)
            )
            btn_wrong.pack(side="right", fill="x", expand=True, padx=(4, 0))
            self.bind_button_hover(btn_wrong, ACCENT_RED, "#e0372d")

    def show_srs_card_details(self):
        """Displays hidden details inside reviews card."""
        self.srs_show_details = True
        self.render_srs_flashcard_state()

    def submit_srs_evaluation(self, is_correct):
        """Applies history, updates SRS levels, schedules next review date, and triggers audio response."""
        card_data = self.srs_queue[self.srs_current_idx]
        kanji_key = card_data["kanji"]
        
        # Save stats and history updates
        stats = self.kanji_db.setdefault("stats", {"total_reviewed": 0, "total_correct": 0})
        stats["total_reviewed"] += 1
        if is_correct:
            stats["total_correct"] += 1
            
        vocab = self.kanji_db.get("vocab", {})
        if kanji_key in vocab:
            vocab[kanji_key].setdefault("history", []).append({
                "date": datetime.now().isoformat(),
                "correct": is_correct
            })
            
            # Recalculate SRS Stage Levels
            current_stage = vocab[kanji_key].get("srs_stage", 1)
            if is_correct:
                next_stage = min(5, current_stage + 1)
                vocab[kanji_key]["srs_stage"] = next_stage
                # Next review delays based on stage
                days_delay = [1, 2, 4, 7, 14, 30][next_stage]
                vocab[kanji_key]["next_review"] = (datetime.now() + timedelta(days=days_delay)).isoformat()
            else:
                vocab[kanji_key]["srs_stage"] = 1 # Reset SRS to level 1 on mistake
                vocab[kanji_key]["next_review"] = (datetime.now() + timedelta(days=1)).isoformat()
                
        guardian.save_kanji_data(self.kanji_db)
        
        # Play speech feedback sound
        if is_correct:
            guardian.speak_japanese_text("せいかい！ 正解")
        else:
            guardian.speak_japanese_text("まちがい！ 間違い")
            
        # Move forward in reviews queue
        self.srs_current_idx += 1
        self.srs_show_details = False
        
        # Redraw
        self.update_sidebar_stats()
        self.render_srs_flashcard_state()

    # ==================== HOVER MOUSE HELPMATES ====================
    def bind_button_hover(self, button, bg_normal, bg_hover):
        def enter(e):
            if button.cget("state") != "disabled":
                button.config(bg=bg_hover)
        def leave(e):
            if button.cget("state") != "disabled":
                button.config(bg=bg_normal)
        button.bind("<Enter>", enter)
        button.bind("<Leave>", leave)

    def bind_hover_highlight(self, widget, bg_normal, bg_hover):
        def enter(e):
            widget.config(bg=bg_hover)
            for child in widget.winfo_children():
                if not isinstance(child, (tk.Button, tk.Canvas)):
                    try:
                        child.config(bg=bg_hover)
                    except tk.TclError:
                        pass
        def leave(e):
            widget.config(bg=bg_normal)
            for child in widget.winfo_children():
                if not isinstance(child, (tk.Button, tk.Canvas)):
                    try:
                        child.config(bg=bg_normal)
                    except tk.TclError:
                        pass
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
        for child in widget.winfo_children():
            if not isinstance(child, (tk.Button, tk.Canvas)):
                child.bind("<Enter>", enter)
                child.bind("<Leave>", leave)

    def change_difficulty(self, new_level):
        """Updates global difficulty and resets/refreshes the current view."""
        self.difficulty_level = new_level
        self.update_difficulty_buttons()
        self.switch_view(self.current_view_key)

    def update_difficulty_buttons(self):
        """Updates segmented difficulty buttons highlights in the sidebar."""
        for level, btn in self.diff_buttons.items():
            if level == self.difficulty_level:
                btn.config(bg=BG_INNER, fg=ACCENT_CYAN)
            else:
                btn.config(bg=BG_CARD, fg=FG_SECONDARY)

    def draw_learn_kanji(self):
        """Renders the Dual-Column interactive JLPT Kanji unlocking room."""
        body = tk.Frame(self.content_frame, bg=BG_DARK)
        body.pack(fill="both", expand=True)
        
        # 1. Left panel: list of curated JLPT level kanji & AI button
        left_panel = tk.Frame(body, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, width=320)
        left_panel.pack(side="left", fill="both")
        left_panel.pack_propagate(False)
        
        lbl_head = tk.Label(
            left_panel,
            text=f"📚 JLPT {self.difficulty_level} CURRICULUM",
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 10, "bold"),
            pady=10
        )
        lbl_head.pack()
        
        ai_btn_text = "⌛ FETCHING AI KANJI..." if self.learn_api_in_progress else "✨ GENERATE NEW KANJI (AI)"
        self.btn_ai_gen = tk.Button(
            left_panel,
            text=ai_btn_text,
            bg=BG_INNER,
            fg=ACCENT_PURPLE,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            pady=10,
            cursor="hand2" if not self.learn_api_in_progress else "arrow",
            command=self.generate_learn_kanji_ai,
            state="disabled" if self.learn_api_in_progress else "normal"
        )
        self.btn_ai_gen.pack(fill="x", padx=10, pady=(0, 10))
        if not self.learn_api_in_progress:
            self.bind_button_hover(self.btn_ai_gen, BG_INNER, HOVER_COLOR)
            
        scroll_container = tk.Frame(left_panel, bg=BG_CARD)
        scroll_container.pack(fill="both", expand=True, padx=5, pady=(0, 10))
        
        list_canvas = tk.Canvas(scroll_container, bg=BG_CARD, highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_container, orient="vertical", command=list_canvas.yview)
        list_frame = tk.Frame(list_canvas, bg=BG_CARD)
        
        list_frame.bind(
            "<Configure>",
            lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all"))
        )
        list_canvas.create_window((0, 0), window=list_frame, anchor="nw", width=290)
        list_canvas.configure(yscrollcommand=scrollbar.set)
        
        list_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def _on_scroll(event):
            if event.delta:
                list_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        list_canvas.bind("<MouseWheel>", _on_scroll)
        
        vocab = self.kanji_db.get("vocab", {})
        curriculum_pool = JLPT_KANJI_DATABASE.get(self.difficulty_level, [])
        
        if curriculum_pool and (not self.active_learn_kanji or self.active_learn_kanji.get("level") != self.difficulty_level):
            unstudied = [k for k in curriculum_pool if k["kanji"] not in vocab]
            if unstudied:
                self.active_learn_kanji = unstudied[0]
            else:
                self.active_learn_kanji = curriculum_pool[0]
                
        for item in curriculum_pool:
            k = item.get("kanji")
            meaning = item.get("meaning")
            is_studied = k in vocab
            
            status_symbol = "✓" if is_studied else "🔒"
            status_color = ACCENT_GREEN if is_studied else FG_SECONDARY
            
            is_active = self.active_learn_kanji and self.active_learn_kanji.get("kanji") == k
            bg_c = HOVER_COLOR if is_active else BG_CARD
            border_c = ACCENT_CYAN if is_active else BORDER_COLOR
            
            row = tk.Frame(
                list_frame,
                bg=bg_c,
                pady=10,
                padx=12,
                highlightbackground=border_c,
                highlightthickness=1,
                cursor="hand2"
            )
            row.pack(fill="x", pady=2)
            
            lbl_sym = tk.Label(row, text=status_symbol, fg=status_color, bg=bg_c, font=(FONT_FAMILY, 10, "bold"))
            lbl_sym.pack(side="left", padx=2)
            
            lbl_k = tk.Label(row, text=k, fg=ACCENT_CYAN, bg=bg_c, font=(FONT_FAMILY, 14, "bold"))
            lbl_k.pack(side="left", padx=10)
            
            lbl_m = tk.Label(row, text=meaning[:15], fg=FG_LIGHT, bg=bg_c, font=(FONT_FAMILY, 8, "bold"))
            lbl_m.pack(side="left", padx=5)
            
            def make_select_cmd(target_item=item):
                def select_action(e):
                    self.active_learn_kanji = target_item
                    self.switch_view("learn_kanji")
                return select_action
                
            row.bind("<Button-1>", make_select_cmd(item))
            for child in row.winfo_children():
                child.bind("<Button-1>", make_select_cmd(item))
                child.bind("<MouseWheel>", _on_scroll)
            row.bind("<MouseWheel>", _on_scroll)
            self.bind_hover_highlight(row, bg_c, HOVER_COLOR)
            
        self.right_learn_pane = tk.Frame(body, bg=BG_DARK, padx=15)
        self.right_learn_pane.pack(side="right", fill="both", expand=True)
        
        self.render_learn_details_pane()

    def generate_learn_kanji_ai(self):
        """Asynchronously calls Gemini API to fetch an unstudied progressive Kanji card."""
        if self.learn_api_in_progress:
            return
            
        self.learn_api_in_progress = True
        self.btn_ai_gen.config(text="⌛ FETCHING AI KANJI...", state="disabled")
        
        studied_list = list(self.kanji_db.get("vocab", {}).keys())
        
        def run_ai():
            api_key = self.config.get("gemini_api_key", "").strip()
            new_card = guardian.get_gemini_kanji_card(api_key, self.difficulty_level, studied_list)
            self.root.after(0, lambda: self.on_ai_kanji_resolved(new_card))
            
        threading.Thread(target=run_ai, daemon=True).start()

    def on_ai_kanji_resolved(self, new_card):
        """Invoked when Gemini returns the progressive Kanji card."""
        self.learn_api_in_progress = False
        if not new_card:
            messagebox.showerror("Error", "Failed to generate new progressive Kanji. Please check internet connection or API keys.", parent=self.root)
            self.switch_view("learn_kanji")
            return
            
        self.active_learn_kanji = new_card
        self.switch_view("learn_kanji")
        messagebox.showinfo("✨ Progressive AI Kanji", f"AI has generated a new progressive Kanji card for you: '{new_card.get('kanji')}'!\nReview the details on the right and click Learn to add it to your deck.", parent=self.root)

    def render_learn_details_pane(self):
        """Renders the detailed interactive info-card panel for learning."""
        for child in self.right_learn_pane.winfo_children():
            child.destroy()
            
        if not self.active_learn_kanji:
            no_card = tk.Frame(self.right_learn_pane, bg=BG_DARK, pady=100)
            no_card.pack(fill="both", expand=True)
            tk.Label(
                no_card,
                text="🎓 Study Card Empty",
                fg=FG_SECONDARY,
                bg=BG_DARK,
                font=(FONT_FAMILY, 14, "bold")
            ).pack()
            tk.Label(
                no_card,
                text="Select a Kanji from the left list to review detailed explanations.",
                fg=FG_SECONDARY,
                bg=BG_DARK,
                font=(FONT_FAMILY, 9)
            ).pack(pady=4)
            return
            
        item = self.active_learn_kanji
        k = item.get("kanji")
        vocab = self.kanji_db.get("vocab", {})
        is_learned = k in vocab
        
        card_frame = tk.Frame(
            self.right_learn_pane,
            bg=BG_CARD,
            padx=25,
            pady=25,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        card_frame.pack(fill="both", expand=True)
        
        left_header = tk.Frame(card_frame, bg=BG_CARD)
        left_header.pack(fill="x")
        
        kanji_lbl = tk.Label(
            left_header,
            text=k,
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 64, "bold"),
            cursor="hand2"
        )
        kanji_lbl.pack(side="left", padx=(0, 20))
        HoverTooltip(kanji_lbl, lambda: item.get("kanji_romaji", ""))
        
        details_col = tk.Frame(left_header, bg=BG_CARD)
        details_col.pack(side="left", fill="y", pady=10)
        
        lbl_meaning = tk.Label(
            details_col,
            text=item.get("meaning", "").upper(),
            fg=BG_INNER,
            bg=BG_CARD,
            font=(FONT_FAMILY, 16, "bold"),
            justify="left"
        )
        lbl_meaning.pack(anchor="w")
        
        lbl_yomi = tk.Label(
            details_col,
            text=f"読み: {item.get('kanji_yomi', '')}",
            fg=BG_INNER,
            bg=BG_CARD,
            font=(FONT_FAMILY, 11, "bold")
        )
        lbl_yomi.pack(anchor="w", pady=2)
        HoverTooltip(lbl_yomi, lambda: item.get("kanji_romaji", ""))
        
        readings_frame = tk.Frame(card_frame, bg=BG_INNER, padx=15, pady=12, highlightbackground=BORDER_COLOR, highlightthickness=1)
        readings_frame.pack(fill="x", pady=15)
        
        onyomi = item.get("onyomi", "")
        onyomi_txt = f"音読み (Onyomi): {onyomi}" if onyomi else "音読み (Onyomi): (none)"
        lbl_on = tk.Label(readings_frame, text=onyomi_txt, fg=BG_INNER, bg=BG_INNER, font=(FONT_FAMILY, 9, "bold"))
        lbl_on.pack(anchor="w")
        
        kunyomi = item.get("kunyomi", "")
        kunyomi_txt = f"訓読み (Kunyomi): {kunyomi}" if kunyomi else "訓読み (Kunyomi): (none)"
        lbl_kun = tk.Label(readings_frame, text=kunyomi_txt, fg=BG_INNER, bg=BG_INNER, font=(FONT_FAMILY, 9, "bold"))
        lbl_kun.pack(anchor="w", pady=(4, 0))
        
        example_frame = tk.Frame(card_frame, bg=BG_CARD)
        example_frame.pack(fill="x", pady=10)
        
        tk.Label(
            example_frame,
            text="例句 (EXAMPLE SENTENCE)",
            fg=ACCENT_PURPLE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        ).pack(anchor="w")
        
        sentence_box = tk.Frame(example_frame, bg=BG_INNER, padx=15, pady=15, highlightbackground=BORDER_COLOR, highlightthickness=1)
        sentence_box.pack(fill="x", pady=6)
        
        lbl_sentence_ja = tk.Label(
            sentence_box,
            text=item.get("example_ja"),
            fg=BG_INNER,
            bg=BG_INNER,
            font=(FONT_FAMILY, 12),
            wraplength=450,
            justify="left"
        )
        lbl_sentence_ja.pack(anchor="w")
        HoverTooltip(lbl_sentence_ja, lambda: item.get("example_romaji", ""))
        
        lbl_sentence_en = tk.Label(
            sentence_box,
            text=item.get("example_en"),
            fg=BG_INNER,
            bg=BG_INNER,
            font=(FONT_FAMILY, 9, "italic"),
            wraplength=450,
            justify="left"
        )
        lbl_sentence_en.pack(anchor="w", pady=(4, 0))
        
        audio_row = tk.Frame(card_frame, bg=BG_CARD)
        audio_row.pack(fill="x", pady=10)
        
        btn_pron_k = tk.Button(
            audio_row,
            text="🔊 PRONOUNCE KANJI",
            bg=BG_INNER,
            fg=ACCENT_CYAN,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=12,
            pady=8,
            cursor="hand2",
            command=lambda: guardian.speak_japanese_text(item.get("kanji_yomi", item.get("kanji")))
        )
        btn_pron_k.pack(side="left", padx=2)
        self.bind_button_hover(btn_pron_k, BG_INNER, HOVER_COLOR)
        
        btn_pron_s = tk.Button(
            audio_row,
            text="🔊 PRONOUNCE SENTENCE",
            bg=BG_INNER,
            fg=ACCENT_CYAN,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=12,
            pady=8,
            cursor="hand2",
            command=lambda: guardian.speak_japanese_text(item.get("example_ja"))
        )
        btn_pron_s.pack(side="left", padx=2)
        self.bind_button_hover(btn_pron_s, BG_INNER, HOVER_COLOR)
        
        bottom_action_frame = tk.Frame(card_frame, bg=BG_CARD)
        bottom_action_frame.pack(fill="x", side="bottom", pady=(10, 0))
        
        if is_learned:
            lbl_learned_badge = tk.Label(
                bottom_action_frame,
                text="✓  ALREADY ADDED TO STUDY DECK",
                fg=ACCENT_GREEN,
                bg=BG_INNER,
                font=(FONT_FAMILY, 10, "bold"),
                pady=12,
                highlightbackground=BORDER_COLOR,
                highlightthickness=1
            )
            lbl_learned_badge.pack(fill="x")
        else:
            self.btn_learn_unlock = tk.Button(
                bottom_action_frame,
                text="🎓 LEARN & ADD TO DECK",
                bg=ACCENT_GREEN,
                fg=FG_LIGHT,
                activebackground="#2aa848",
                bd=0,
                font=(FONT_FAMILY, 10, "bold"),
                pady=12,
                cursor="hand2",
                command=self.learn_active_kanji
            )
            self.btn_learn_unlock.pack(fill="x")
            self.bind_button_hover(self.btn_learn_unlock, ACCENT_GREEN, "#2aa848")
            
        widgets_to_fade = [
            (lbl_meaning, FG_LIGHT),
            (lbl_yomi, FG_SECONDARY),
            (lbl_on, ACCENT_ORANGE),
            (lbl_kun, ACCENT_GREEN),
            (lbl_sentence_ja, FG_LIGHT),
            (lbl_sentence_en, FG_SECONDARY)
        ]
        self.animate_text_fade(widgets_to_fade)

    def learn_active_kanji(self):
        """Unlocks and adds the active Kanji to study deck progress database."""
        if not self.active_learn_kanji:
            return
            
        item = self.active_learn_kanji
        k = item.get("kanji")
        vocab = self.kanji_db.setdefault("vocab", {})
        
        if k in vocab:
            return
            
        vocab[k] = {
            "kanji": k,
            "meaning": item.get("meaning"),
            "onyomi": item.get("onyomi"),
            "kunyomi": item.get("kunyomi"),
            "stroke_count": item.get("stroke_count", len(k)),
            "example_ja": item.get("example_ja"),
            "example_en": item.get("example_en"),
            "kanji_yomi": item.get("kanji_yomi", ""),
            "kanji_romaji": item.get("kanji_romaji", ""),
            "example_yomi": item.get("example_yomi", item.get("kanji_yomi", "")),
            "example_romaji": item.get("example_romaji", item.get("kanji_romaji", "")),
            "level": item.get("level", self.difficulty_level),
            "srs_stage": 1,
            "next_review": (datetime.now() + timedelta(days=1)).isoformat(),
            "history": []
        }
        
        guardian.save_kanji_data(self.kanji_db)
        guardian.speak_japanese_text(f"覚えた！ {k}")
        self.switch_view("learn_kanji")
        messagebox.showinfo("🎉 UNLOCKED!", f"Successfully unlocked '{k}'! It has been added to your SRS Review Deck.", parent=self.root)

    def draw_ai_conversation(self):
        """Renders the Premium Apple AI Sensei Conversation Room."""
        body = tk.Frame(self.content_frame, bg=BG_DARK)
        body.pack(fill="both", expand=True)
        
        top_bar = tk.Frame(body, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, pady=8, padx=15)
        top_bar.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            top_bar,
            text="💬 PRACTICE SCENARIO:",
            fg=FG_SECONDARY,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        ).pack(side="left", padx=(0, 10))
        
        scenarios = list(OFFLINE_CONVERSATION_TREES.keys())
        self.scenario_var = tk.StringVar(value=self.active_scenario)
        
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TCombobox", fieldbackground=BG_INNER, background=BG_INNER, foreground=FG_LIGHT, darkcolor=BG_INNER, lightcolor=BG_INNER, bordercolor=BORDER_COLOR)
        
        self.scenario_combo = ttk.Combobox(
            top_bar,
            textvariable=self.scenario_var,
            values=scenarios,
            state="readonly",
            width=28,
            font=(FONT_FAMILY, 9)
        )
        self.scenario_combo.pack(side="left")
        self.scenario_combo.bind("<<ComboboxSelected>>", lambda e: self.reset_conversation())
        
        btn_reset = tk.Button(
            top_bar,
            text="↻  RESET CHAT",
            bg=BG_INNER,
            fg=ACCENT_RED,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.reset_conversation
        )
        btn_reset.pack(side="right")
        self.bind_button_hover(btn_reset, BG_INNER, HOVER_COLOR)
        
        self.chat_container = tk.Frame(body, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1)
        self.chat_container.pack(fill="both", expand=True)
        
        self.chat_canvas = tk.Canvas(self.chat_container, bg=BG_CARD, highlightthickness=0)
        self.chat_scrollbar = tk.Scrollbar(self.chat_container, orient="vertical", command=self.chat_canvas.yview)
        self.chat_frame = tk.Frame(self.chat_canvas, bg=BG_CARD)
        
        self.chat_frame.bind(
            "<Configure>",
            lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        )
        self.chat_canvas.create_window((0, 0), window=self.chat_frame, anchor="nw", width=700)
        self.chat_canvas.configure(yscrollcommand=self.chat_scrollbar.set)
        
        self.chat_canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        self.chat_scrollbar.pack(side="right", fill="y")
        
        def _on_chat_scroll(event):
            if event.delta:
                self.chat_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.chat_canvas.bind("<MouseWheel>", _on_chat_scroll)
        
        self.bottom_control_frame = tk.Frame(body, bg=BG_DARK, pady=10)
        self.bottom_control_frame.pack(fill="x")
        
        if not self.chat_history:
            self.reset_conversation(first_time=True)
        else:
            self.render_chat_bubbles()
            self.render_bottom_controls()

    def reset_conversation(self, first_time=False):
        """Resets the chat log and state for the chosen scenario."""
        if not first_time:
            self.active_scenario = self.scenario_var.get()
            
        self.chat_history = []
        self.active_offline_node = "start"
        
        api_key = self.config.get("gemini_api_key", "").strip()
        if api_key:
            welcomes = {
                "At a Japanese Restaurant": "いらっしゃいませ！レストランへようこそ。ご注文はお決まりですか？ (Welcome! Are you ready to order?)",
                "Asking for Directions": "すみません、何かお困りですか？どこへ行きたいですか？ (Excuse me, do you need help? Where would you like to go?)",
                "Checking in at a Hotel": "いらっしゃいませ。ホテルへようこそ。チェックインをお願いします。(Welcome to the hotel. Please check in.)",
                "Casual Talk with Friends": "ヤッホー！最近どう？元気にしてる？(Hey! How's it going lately?)"
            }
            self.chat_history.append({
                "sender": "ai",
                "text": welcomes.get(self.active_scenario, "こんにちは！日本語で話しましょう。"),
                "yomi": "",
                "romaji": "",
                "en": "",
                "corrections": None
            })
        else:
            tree = OFFLINE_CONVERSATION_TREES.get(self.active_scenario, {})
            start_node = tree.get("start", {})
            if start_node:
                self.chat_history.append({
                    "sender": "ai",
                    "text": start_node.get("ai_reply"),
                    "yomi": start_node.get("ai_yomi", ""),
                    "romaji": start_node.get("ai_romaji", ""),
                    "en": start_node.get("ai_en", ""),
                    "corrections": None
                })
                
        if self.chat_history:
            greeting_text = self.chat_history[0]["text"]
            if " (" in greeting_text:
                greeting_text = greeting_text.split(" (")[0]
            guardian.speak_japanese_text(greeting_text)
            
        if not first_time:
            self.render_chat_bubbles()
            self.render_bottom_controls()

    def render_chat_bubbles(self):
        """Renders the Premium Apple AI Sensei Chat history and explanation cards."""
        for child in self.chat_frame.winfo_children():
            child.destroy()
            
        for msg_idx, msg in enumerate(self.chat_history):
            sender = msg["sender"]
            text = msg["text"]
            
            # Wrapper for this message bubble & potential explanation card
            bubble_container = tk.Frame(self.chat_frame, bg=BG_CARD, pady=6)
            bubble_container.pack(fill="x", expand=True)
            
            # Check sender to align left (Sensei) or right (User)
            if sender == "ai":
                # Sensei bubble
                header_frame = tk.Frame(bubble_container, bg=BG_CARD)
                header_frame.pack(fill="x", anchor="w")
                
                avatar_lbl = tk.Label(
                    header_frame,
                    text="🎓  Sensei",
                    fg=ACCENT_CYAN,
                    bg=BG_CARD,
                    font=(FONT_FAMILY, 9, "bold")
                )
                avatar_lbl.pack(side="left")
                
                # Action buttons next to header
                actions_frame = tk.Frame(header_frame, bg=BG_CARD)
                actions_frame.pack(side="right")
                
                # Play audio button
                def make_speak_cmd(t=text):
                    clean_t = t
                    if " (" in clean_t:
                        clean_t = clean_t.split(" (")[0]
                    return lambda: guardian.speak_japanese_text(clean_t)
                    
                btn_speak = tk.Button(
                    actions_frame,
                    text="🔊",
                    bg=BG_CARD,
                    fg=ACCENT_CYAN,
                    activebackground=HOVER_COLOR,
                    activeforeground=FG_LIGHT,
                    bd=0,
                    font=(FONT_FAMILY, 8),
                    cursor="hand2",
                    padx=4,
                    command=make_speak_cmd(text)
                )
                btn_speak.pack(side="left", padx=4)
                HoverTooltip(btn_speak, lambda: "Speak sentence out loud")
                
                # Explain button
                explain_text = "💡 EXPLAINING..." if msg_idx in self.explaining_message_ids else "💡 EXPLAIN"
                explain_state = "disabled" if msg_idx in self.explaining_message_ids else "normal"
                
                def make_explain_cmd(idx=msg_idx):
                    return lambda: self.toggle_deep_explanation(idx)
                    
                btn_explain = tk.Button(
                    actions_frame,
                    text=explain_text,
                    bg=BG_CARD,
                    fg=ACCENT_PURPLE,
                    activebackground=HOVER_COLOR,
                    activeforeground=FG_LIGHT,
                    bd=0,
                    font=(FONT_FAMILY, 8, "bold"),
                    cursor="hand2" if msg_idx not in self.explaining_message_ids else "arrow",
                    padx=4,
                    command=make_explain_cmd(msg_idx),
                    state=explain_state
                )
                btn_explain.pack(side="left", padx=4)
                HoverTooltip(btn_explain, lambda: "Get deep grammar & vocabulary breakdown")
                
                # Bubble contents
                bubble = tk.Frame(
                    bubble_container,
                    bg=BG_INNER,
                    highlightbackground=BORDER_COLOR,
                    highlightthickness=1,
                    padx=12,
                    pady=10
                )
                bubble.pack(fill="x", anchor="w", pady=(4, 0))
                
                # Main Japanese reply text
                lbl_ja = tk.Label(
                    bubble,
                    text=text,
                    fg=FG_LIGHT,
                    bg=BG_INNER,
                    font=(FONT_FAMILY, 11),
                    anchor="w",
                    justify="left",
                    wraplength=640
                )
                lbl_ja.pack(fill="x", anchor="w")
                
                # Yomi / Romaji readings (if available)
                readings_str = []
                if msg.get("yomi"):
                    readings_str.append(f"Yomi: {msg['yomi']}")
                if msg.get("romaji"):
                    readings_str.append(f"Romaji: {msg['romaji']}")
                if msg.get("en"):
                    readings_str.append(f"English: {msg['en']}")
                    
                if readings_str:
                    readings_lbl = tk.Label(
                        bubble,
                        text="\n".join(readings_str),
                        fg=FG_SECONDARY,
                        bg=BG_INNER,
                        font=(FONT_FAMILY, 8),
                        anchor="w",
                        justify="left",
                        wraplength=640
                    )
                    readings_lbl.pack(fill="x", anchor="w", pady=(8, 0))
                    
                # Grammar corrections (if present)
                if msg.get("corrections"):
                    corr_lbl = tk.Label(
                        bubble,
                        text=f"📝 Sensei's Feedback:\n{msg['corrections']}",
                        fg=ACCENT_ORANGE,
                        bg=BG_INNER,
                        font=(FONT_FAMILY, 8, "italic"),
                        anchor="w",
                        justify="left",
                        wraplength=640
                    )
                    corr_lbl.pack(fill="x", anchor="w", pady=(8, 0))
                    
                # If expanded explanation exists, show explanation card
                if msg_idx in self.expanded_explanations:
                    explanation = self.message_explanations.get(msg_idx)
                    if explanation:
                        explain_frame = tk.Frame(
                            bubble_container,
                            bg="#1C1C1E",
                            highlightbackground="#2C2C2E",
                            highlightthickness=1,
                            padx=15,
                            pady=12
                        )
                        explain_frame.pack(fill="x", anchor="w", pady=(8, 0))
                        
                        # Header row with title & close button
                        title_row = tk.Frame(explain_frame, bg="#1C1C1E")
                        title_row.pack(fill="x", anchor="w", pady=(0, 6))
                        
                        lbl_title = tk.Label(
                            title_row,
                            text="💡 DEEP LINGUISTIC BREAKDOWN",
                            fg=ACCENT_PURPLE,
                            bg="#1C1C1E",
                            font=(FONT_FAMILY, 9, "bold")
                        )
                        lbl_title.pack(side="left")
                        
                        btn_close = tk.Button(
                            title_row,
                            text="✕",
                            bg="#1C1C1E",
                            fg=FG_SECONDARY,
                            activebackground="#2C2C2E",
                            activeforeground=FG_LIGHT,
                            bd=0,
                            font=(FONT_FAMILY, 9, "bold"),
                            cursor="hand2",
                            command=make_explain_cmd(msg_idx)
                        )
                        btn_close.pack(side="right")
                        
                        lines = explanation.split("\n")
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                            if line.startswith("###"):
                                title_sec = line.replace("###", "").strip()
                                lbl_sec = tk.Label(
                                    explain_frame,
                                    text=title_sec,
                                    fg=ACCENT_CYAN,
                                    bg="#1C1C1E",
                                    font=(FONT_FAMILY, 10, "bold"),
                                    anchor="w",
                                    justify="left"
                                )
                                lbl_sec.pack(fill="x", anchor="w", pady=(8, 4))
                            elif line.startswith("-"):
                                bullet_text = line.replace("-", "").strip()
                                lbl_bullet = tk.Label(
                                    explain_frame,
                                    text=f"  •  {bullet_text}",
                                    fg=FG_LIGHT,
                                    bg="#1C1C1E",
                                    font=(FONT_FAMILY, 9),
                                    anchor="w",
                                    justify="left",
                                    wraplength=640
                                )
                                lbl_bullet.pack(fill="x", anchor="w", pady=2)
                            else:
                                lbl_norm = tk.Label(
                                    explain_frame,
                                    text=line,
                                    fg=FG_LIGHT,
                                    bg="#1C1C1E",
                                    font=(FONT_FAMILY, 9),
                                    anchor="w",
                                    justify="left",
                                    wraplength=640
                                )
                                lbl_norm.pack(fill="x", anchor="w", pady=2)
                    elif msg_idx in self.explaining_message_ids:
                        # Loader frame
                        loader_frame = tk.Frame(
                            bubble_container,
                            bg="#1C1C1E",
                            highlightbackground="#2C2C2E",
                            highlightthickness=1,
                            padx=15,
                            pady=15
                        )
                        loader_frame.pack(fill="x", anchor="w", pady=(8, 0))
                        
                        lbl_loader = tk.Label(
                            loader_frame,
                            text="⌛ Analyzing grammar patterns and fetching deep linguistic context from Gemini...",
                            fg=FG_SECONDARY,
                            bg="#1C1C1E",
                            font=(FONT_FAMILY, 9, "italic"),
                            anchor="w"
                        )
                        lbl_loader.pack(fill="x", anchor="w")
                        
            else:
                # User bubble (aligned right)
                header_frame = tk.Frame(bubble_container, bg=BG_CARD)
                header_frame.pack(fill="x", anchor="e")
                
                avatar_lbl = tk.Label(
                    header_frame,
                    text="Student  👤",
                    fg=ACCENT_CYAN,
                    bg=BG_CARD,
                    font=(FONT_FAMILY, 9, "bold")
                )
                avatar_lbl.pack(side="right")
                
                bubble = tk.Frame(
                    bubble_container,
                    bg="#0071E3", # Apple Royal Blue
                    padx=12,
                    pady=10
                )
                bubble.pack(fill="x", anchor="e", pady=(4, 0))
                
                lbl_user = tk.Label(
                    bubble,
                    text=text,
                    fg=FG_LIGHT,
                    bg="#0071E3",
                    font=(FONT_FAMILY, 11),
                    anchor="e",
                    justify="right",
                    wraplength=640
                )
                lbl_user.pack(fill="x", anchor="e")
                
        # Auto scroll to bottom
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    def start_voice_recording(self):
        """Starts dynamic microphone voice recording via native winmm.dll asynchronously."""
        if self.voice_recording_in_progress or self.chat_api_in_progress:
            return
            
        self.voice_recording_in_progress = True
        self.voice_recording_seconds = 5
        self.render_bottom_controls()
        
        output_path = os.path.abspath("temp_voice.wav")
        
        def run_recording():
            import subprocess
            import os
            
            # Clean up old voice recording if exists
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass
                    
            ps_commands = f"""
$memberDefinition = @'
[DllImport("winmm.dll", EntryPoint="mciSendStringA", CharSet=CharSet.Ansi)]
public static extern int mciSendString(string lpstrCommand, System.Text.StringBuilder lpstrReturnString, int uReturnLength, IntPtr hwndCallback);
'@
$winaudio = Add-Type -MemberDefinition $memberDefinition -Name "WinAudio" -Namespace "WinMM" -PassThru
[void]$winaudio::mciSendString("open new type waveaudio alias recsound", $null, 0, [System.IntPtr]::Zero)
[void]$winaudio::mciSendString("record recsound", $null, 0, [System.IntPtr]::Zero)
Start-Sleep -Seconds 5
[void]$winaudio::mciSendString("save recsound \\`"{output_path}\\`"", $null, 0, [System.IntPtr]::Zero)
[void]$winaudio::mciSendString("close recsound", $null, 0, [System.IntPtr]::Zero)
"""
            try:
                subprocess.run(
                    ["powershell", "-Command", ps_commands],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
            except Exception as e:
                print(f"Subprocess recording failed: {e}")
                
            self.root.after(0, self.finish_voice_recording)
            
        # Start the countdown timer in Tkinter
        self.tick_voice_countdown()
        
        # Launch background recording thread
        import threading
        threading.Thread(target=run_recording, daemon=True).start()

    def tick_voice_countdown(self):
        """Ticks down recording visual display countdown every second."""
        if not self.voice_recording_in_progress:
            return
        if self.voice_recording_seconds > 1:
            self.voice_recording_seconds -= 1
            self.render_bottom_controls()
            self.root.after(1000, self.tick_voice_countdown)
        else:
            self.voice_recording_seconds = 0

    def finish_voice_recording(self):
        """Completes recording background execution and forwards WAV to Gemini."""
        self.voice_recording_in_progress = False
        self.voice_recording_seconds = 5
        self.render_bottom_controls()
        
        # Verify voice file exists before sending
        if os.path.exists("temp_voice.wav") and os.path.getsize("temp_voice.wav") > 100:
            self.send_custom_chat_message(audio_path="temp_voice.wav")
        else:
            print("Recording file temp_voice.wav was missing or invalid.")

    def toggle_deep_explanation(self, msg_idx):
        """Expands/collapses the detailed grammar and vocab explanation card."""
        if msg_idx in self.expanded_explanations:
            self.expanded_explanations.remove(msg_idx)
            self.render_chat_bubbles()
        else:
            self.expanded_explanations.add(msg_idx)
            if msg_idx not in self.message_explanations:
                msg = self.chat_history[msg_idx]
                if msg.get("ai_explain"):
                    self.message_explanations[msg_idx] = msg["ai_explain"]
                    self.render_chat_bubbles()
                else:
                    api_key = self.config.get("gemini_api_key", "").strip()
                    if api_key:
                        self.explain_message_in_deep(msg_idx, msg["text"])
                    else:
                        explanation = self.find_offline_explanation_for_text(msg["text"])
                        self.message_explanations[msg_idx] = explanation
                        self.render_chat_bubbles()
            else:
                self.render_chat_bubbles()

    def explain_message_in_deep(self, msg_idx, ja_text):
        """Asynchronously queries Gemini for a complete grammatical and vocabulary breakdown."""
        if msg_idx in self.explaining_message_ids:
            return
            
        self.explaining_message_ids.add(msg_idx)
        self.render_chat_bubbles()
        
        def run_explain():
            import requests
            import json
            
            api_key = self.config.get("gemini_api_key", "").strip()
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            
            prompt = (
                f"You are a native Japanese language teacher and linguist.\\n"
                f"Please provide a deep, elegant, and highly structured linguistic breakdown of the following Japanese sentence:\\n"
                f"\\\"{ja_text}\\\"\\n\\n"
                f"Your breakdown must be formatted in beautiful GitHub Markdown (using subheadings and bullet points). Break it down into the following four clear sections:\\n"
                f"1. ### 💡 Grammar & Structure: Detail the overall sentence pattern, clauses, and verb/adjective conjugations.\\n"
                f"2. ### 📖 Vocabulary & Readings: List key vocabulary terms with their kanji, kana, romaji, and English translation.\\n"
                f"3. ### 📌 Particles Used: Analyze each particle used in the sentence (like は, が, を, に, etc.) and explain its specific role.\\n"
                f"4. ### 🎭 Formality & Nuance: Describe the politeness level (Keigo, standard polite, or casual) and any cultural or situational nuances.\\n\\n"
                f"Keep your tone extremely encouraging, clear, and professional. Return only the markdown text response."
            )
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            }
            
            explanation = ""
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=12)
                if response.status_code == 200:
                    res_json = response.json()
                    explanation = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            except Exception as e:
                print(f"Gemini Explanation API call failed: {e}")
                
            if not explanation:
                explanation = "Failed to fetch online explanation. Please check your internet connection."
                
            def resolve():
                self.explaining_message_ids.discard(msg_idx)
                self.message_explanations[msg_idx] = explanation
                self.render_chat_bubbles()
                
            self.root.after(0, resolve)
            
        import threading
        threading.Thread(target=run_explain, daemon=True).start()

    def find_offline_explanation_for_text(self, text):
        """Searches offline conversation trees for matching AI replies to retrieve pre-curated explanations."""
        for scenario, nodes in OFFLINE_CONVERSATION_TREES.items():
            for node_name, node in nodes.items():
                if node.get("ai_reply") == text and node.get("ai_explain"):
                    return node.get("ai_explain")
        return (
            "### 💡 Grammar & Structure\\n"
            "This is an offline fallback breakdown. Learn Japanese grammar patterns to analyze verb conjugations and particle usage.\\n\\n"
            "### 📖 Vocabulary & Readings\\n"
            "Check the Kanji Explorer tab to study readings, strokes, and definitions of the kanji in this sentence.\\n\\n"
            "### 📌 Particles Used\\n"
            "Particles form the backbone of Japanese grammar. Study は, が, を, に, and で to understand sentence relations.\\n\\n"
            "### 🎭 Formality & Nuance\\n"
            "Politeness level is usually polite (Desu/Masu) in customer-service scenarios, or casual in daily friend talks."
        )

    def render_bottom_controls(self):
        """Builds either the text input bar (Online) or the multiple-choice option pills (Offline)."""
        for child in self.bottom_control_frame.winfo_children():
            child.destroy()
            
        api_key = self.config.get("gemini_api_key", "").strip()
        
        if api_key:
            input_container = tk.Frame(self.bottom_control_frame, bg=BG_DARK)
            input_container.pack(fill="x")
            
            entry_state = "disabled" if self.chat_api_in_progress or self.voice_recording_in_progress else "normal"
            btn_state = "disabled" if self.chat_api_in_progress or self.voice_recording_in_progress else "normal"
            btn_text = "⌛ SENDING..." if self.chat_api_in_progress else "✉️  SEND"
            
            self.chat_input = tk.Entry(
                input_container,
                bg=BG_CARD,
                fg=FG_LIGHT,
                insertbackground=FG_LIGHT,
                bd=1,
                relief="flat",
                font=(FONT_FAMILY, 10),
                state=entry_state
            )
            self.chat_input.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=8)
            self.chat_input.bind("<Return>", lambda e: self.send_custom_chat_message())
            
            # Send button
            btn_send = tk.Button(
                input_container,
                text=btn_text,
                bg=ACCENT_CYAN,
                fg=FG_LIGHT,
                activebackground="#147ce5",
                activeforeground=FG_LIGHT,
                bd=0,
                font=(FONT_FAMILY, 9, "bold"),
                padx=15,
                pady=8,
                cursor="hand2" if btn_state == "normal" else "arrow",
                command=self.send_custom_chat_message,
                state=btn_state
            )
            btn_send.pack(side="right")
            if btn_state == "normal":
                self.bind_button_hover(btn_send, ACCENT_CYAN, "#147ce5")
                
            # Microphone Record Voice Button
            if self.voice_recording_in_progress:
                btn_mic_text = f"🔴 REC ({self.voice_recording_seconds}s)"
                btn_mic_bg = "#FF453A"  # Neon Red
                btn_mic_fg = FG_LIGHT
                btn_mic_state = "disabled"
                btn_mic_cmd = None
            else:
                btn_mic_text = "🎙️ RECORD"
                btn_mic_bg = "#BF5AF2"  # Neon Purple
                btn_mic_fg = FG_LIGHT
                btn_mic_state = "disabled" if self.chat_api_in_progress else "normal"
                btn_mic_cmd = self.start_voice_recording

            btn_mic = tk.Button(
                input_container,
                text=btn_mic_text,
                bg=btn_mic_bg,
                fg=btn_mic_fg,
                activebackground="#AC45D6",
                activeforeground=FG_LIGHT,
                bd=0,
                font=(FONT_FAMILY, 9, "bold"),
                padx=15,
                pady=8,
                cursor="hand2" if btn_mic_state == "normal" else "arrow",
                command=btn_mic_cmd,
                state=btn_mic_state
            )
            btn_mic.pack(side="right", padx=(0, 10))
            if btn_mic_state == "normal":
                self.bind_button_hover(btn_mic, btn_mic_bg, "#AC45D6")
            HoverTooltip(btn_mic, lambda: "Record 5s of Japanese speech from microphone")
        else:
            tree = OFFLINE_CONVERSATION_TREES.get(self.active_scenario, {})
            node = tree.get(self.active_offline_node, {})
            choices = node.get("choices", [])
            
            if choices:
                lbl_prompt = tk.Label(
                    self.bottom_control_frame,
                    text="⚡  SELECT YOUR RESPONSE PILL:",
                    fg=ACCENT_CYAN,
                    bg=BG_DARK,
                    font=(FONT_FAMILY, 8, "bold")
                )
                lbl_prompt.pack(anchor="w", pady=(0, 6))
                
                tray = tk.Frame(self.bottom_control_frame, bg=BG_DARK)
                tray.pack(fill="x")
                
                for idx, opt in enumerate(choices):
                    text_disp = opt.get("text")
                    
                    def make_click_cmd(o=opt):
                        return lambda: self.select_offline_choice(o)
                        
                    pill = tk.Button(
                        tray,
                        text=text_disp,
                        bg=BG_CARD,
                        fg=FG_LIGHT,
                        activebackground=HOVER_COLOR,
                        activeforeground=FG_LIGHT,
                        bd=1,
                        highlightbackground=BORDER_COLOR,
                        font=(FONT_FAMILY, 9, "bold"),
                        padx=12,
                        pady=8,
                        cursor="hand2",
                        command=make_click_cmd(opt)
                    )
                    pill.pack(side="left", padx=4)
                    self.bind_button_hover(pill, BG_CARD, HOVER_COLOR)
                    HoverTooltip(pill, lambda o=opt: f"ENGLISH: {o.get('en')}")
            else:
                lbl_end = tk.Label(
                    self.bottom_control_frame,
                    text="🎉 CONVERSATION COMPLETED SUCCESSFULLY!",
                    fg=ACCENT_GREEN,
                    bg=BG_DARK,
                    font=(FONT_FAMILY, 9, "bold")
                )
                lbl_end.pack(anchor="center", pady=10)

    def select_offline_choice(self, opt):
        """Pushes the offline multiple-choice nodes forward and narrates response."""
        self.chat_history.append({
            "sender": "user",
            "text": opt["text"],
            "corrections": None
        })
        
        self.active_offline_node = opt["next_node"]
        
        tree = OFFLINE_CONVERSATION_TREES.get(self.active_scenario, {})
        next_node = tree.get(self.active_offline_node, {})
        
        if next_node:
            self.chat_history.append({
                "sender": "ai",
                "text": next_node.get("ai_reply"),
                "yomi": next_node.get("ai_yomi", ""),
                "romaji": next_node.get("ai_romaji", ""),
                "en": next_node.get("ai_en", ""),
                "corrections": None
            })
            
            guardian.speak_japanese_text(next_node.get("ai_reply"))
            
        self.render_chat_bubbles()
        self.render_bottom_controls()

    def send_custom_chat_message(self, audio_path=None):
        """Sends custom text or audio inputs to the Gemini conversation practice endpoint asynchronously."""
        if self.chat_api_in_progress:
            return
            
        if audio_path:
            text = ""
        else:
            text = self.chat_input.get().strip()
            if not text:
                return
            self.chat_input.delete(0, tk.END)
            
        if audio_path:
            self.chat_history.append({
                "sender": "user",
                "text": "🎙️ [Transcribing Spoken Audio...]",
                "corrections": None,
                "is_audio": True
            })
        else:
            self.chat_history.append({
                "sender": "user",
                "text": text,
                "corrections": None
            })
            
        self.render_chat_bubbles()
        
        self.chat_api_in_progress = True
        self.render_bottom_controls()
        
        def run_api_chat():
            import requests
            import base64
            import json
            import os
            
            api_key = self.config.get("gemini_api_key", "").strip()
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            
            hist_summary = []
            history_subset = self.chat_history[:-1]
            for m in history_subset:
                hist_summary.append(f"{m['sender'].upper()}: {m['text']}")
            hist_str = "\n".join(hist_summary)
            
            if audio_path:
                audio_base64 = ""
                if os.path.exists(audio_path):
                    try:
                        with open(audio_path, "rb") as f:
                            audio_base64 = base64.b64encode(f.read()).decode("utf-8")
                    except Exception as e:
                        print(f"Error encoding audio file: {e}")
                
                prompt = (
                    f"You are Sensei, a native Japanese language teacher having a conversation with a student.\n"
                    f"The active scenario is: '{self.active_scenario}'\n"
                    f"The student just spoke in the attached audio. Please transcribe what they said in Japanese as accurately as possible.\n"
                    f"The student's difficulty level (JLPT) is: '{self.difficulty_level}'\n"
                    f"Here is the recent conversation history:\n{hist_str}\n\n"
                    f"Please respond to the student in natural Japanese matching the scenario and difficulty level.\n"
                    f"Also, review the student's transcription. If they made any spelling, grammatical, or vocabulary mistakes, provide gentle corrections and tips in English. If their message is perfect, say so.\n\n"
                    f"You MUST return a raw JSON object with the following keys. Do NOT wrap in markdown code blocks or add any extra conversational text. Return only the raw JSON string:\n"
                    f"{{\n"
                    f'  "student_transcription": "Your transcription of what the student said in Japanese in the audio (e.g. メニューをください)",\n'
                    f'  "reply_ja": "Your reply in natural Japanese (e.g. はい、どうぞ！)",\n'
                    f'  "reply_yomi": "The hiragana/furigana representation of your reply with spaces separating words for readability (e.g. はい、 どうぞ！)",\n'
                    f'  "reply_romaji": "The romaji reading of your reply with spaces separating words, all lowercase (e.g. hai, douzo!)",\n'
                    f'  "reply_en": "The English translation of your reply",\n'
                    f'  "corrections": "Your evaluation and corrections of the student\'s Japanese input in English. Highlight any mistakes in grammar, spelling, or vocabulary, and comment on their spoken audio if applicable. Be encouraging!"\n'
                    f"}}"
                )
                
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {
                                    "inline_data": {
                                        "mime_type": "audio/wav",
                                        "data": audio_base64
                                    }
                                },
                                {
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                }
            else:
                prompt = (
                    f"You are Sensei, a native Japanese language teacher having a conversation with a student.\n"
                    f"The active scenario is: '{self.active_scenario}'\n"
                    f"The student's difficulty level (JLPT) is: '{self.difficulty_level}'\n"
                    f"The student just said: '{text}'\n"
                    f"Here is the recent conversation history:\n{hist_str}\n\n"
                    f"Please respond to the student in natural Japanese matching the scenario and difficulty level.\n"
                    f"Also, review the student's message. If they made any spelling, grammatical, or vocabulary mistakes, provide gentle corrections and tips in English. If their message is perfect, say so.\n\n"
                    f"You MUST return a raw JSON object with the following keys. Do NOT wrap in markdown code blocks or add any extra conversational text. Return only the raw JSON string:\n"
                    f"{{\n"
                    f'  "reply_ja": "Your reply in natural Japanese (e.g. はい、どうぞ！)",\n'
                    f'  "reply_yomi": "The hiragana/furigana representation of your reply with spaces separating words for readability (e.g. はい、 どうぞ！)",\n'
                    f'  "reply_romaji": "The romaji reading of your reply with spaces separating words, all lowercase (e.g. hai, douzo!)",\n'
                    f'  "reply_en": "The English translation of your reply",\n'
                    f'  "corrections": "Your evaluation and corrections of the student\'s Japanese input in English. Highlight any mistakes in grammar, spelling, or vocabulary and give tips on how to improve. Be encouraging!"\n'
                    f"}}"
                )
                
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt}
                            ]
                        }
                    ]
                }
                
            parsed = None
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=15)
                if response.status_code == 200:
                    res_json = response.json()
                    res_text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                    if res_text.startswith("```json"):
                        res_text = res_text[7:]
                    if res_text.startswith("```"):
                        res_text = res_text[3:]
                    if res_text.endswith("```"):
                        res_text = res_text[:-3]
                    res_text = res_text.strip()
                    parsed = json.loads(res_text)
            except Exception as e:
                print(f"Gemini Chat API call failed: {e}")
                
            self.root.after(0, lambda: self.on_api_chat_resolved(parsed))
            
        import threading
        threading.Thread(target=run_api_chat, daemon=True).start()

    def on_api_chat_resolved(self, parsed):
        """Invoked when Gemini returns the conversational chat reply and feedback."""
        self.chat_api_in_progress = False
        
        # If there's a transcription in the parsed response, update the last user message
        if parsed and "student_transcription" in parsed and parsed["student_transcription"]:
            for msg in reversed(self.chat_history):
                if msg["sender"] == "user" and msg.get("is_audio"):
                    msg["text"] = f"🎙️ Spoken: \"{parsed['student_transcription']}\""
                    break
                    
        if parsed and "reply_ja" in parsed:
            self.chat_history.append({
                "sender": "ai",
                "text": parsed["reply_ja"],
                "yomi": parsed.get("reply_yomi", ""),
                "romaji": parsed.get("reply_romaji", ""),
                "en": parsed.get("reply_en", ""),
                "corrections": parsed.get("corrections", "")
            })
            guardian.speak_japanese_text(parsed["reply_ja"])
        else:
            # Fallback if transcription failed but we had a user placeholder
            for msg in reversed(self.chat_history):
                if msg["sender"] == "user" and msg.get("is_audio") and msg["text"].startswith("🎙️ ["):
                    msg["text"] = "🎙️ Spoken: [Audio input]"
                    break
                    
            fallback_text = "すみません、聞き取れませんでした。もう一度言ってください。(Sorry, I couldn't hear that. Please say it again.)"
            self.chat_history.append({
                "sender": "ai",
                "text": fallback_text,
                "yomi": "",
                "romaji": "",
                "en": "",
                "corrections": "Gemini connection error. Offline fallback used."
            })
            guardian.speak_japanese_text("すみません、聞き取れませんでした。もう一度言ってください。")
            
        self.render_chat_bubbles()
        self.render_bottom_controls()

    def interpolate_color(self, color1, color2, step, total_steps=10):
        """Linearly interpolates between two hex colors at a specific step."""
        c1 = [int(color1[i:i+2], 16) for i in (1, 3, 5)]
        c2 = [int(color2[i:i+2], 16) for i in (1, 3, 5)]
        curr = [int(c1[j] + (c2[j] - c1[j]) * (step / total_steps)) for j in range(3)]
        return f"#{curr[0]:02x}{curr[1]:02x}{curr[2]:02x}"

    def animate_text_fade(self, widgets_to_fade, bg_fade_widgets=None, step=0):
        """Linearly interpolates text/bg colors over 10 steps (15ms intervals) to complete in 150ms."""
        total_steps = 10
        if step > total_steps:
            return
            
        for widget, target_fg in widgets_to_fade:
            try:
                if widget.winfo_exists():
                    curr_fg = self.interpolate_color(BG_INNER, target_fg, step, total_steps)
                    widget.config(fg=curr_fg)
            except Exception:
                pass
                
        self.root.after(15, lambda: self.animate_text_fade(widgets_to_fade, bg_fade_widgets, step + 1))

        for child in widget.winfo_children():
            if not isinstance(child, (tk.Button, tk.Canvas)):
                child.bind("<Enter>", enter)
                child.bind("<Leave>", leave)


# ==================== SCRIPT ENTRYPOINT ====================
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = JapaneseLearningApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Japanese Learning standalone crash: {e}")
