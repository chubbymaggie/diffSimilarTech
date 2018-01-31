import os.path
import pickle
from prepros import get_words
import pymysql.cursors
import sys
import time

start_time = time.time()
compa_sent_count = 0
total_sent_count = 0
post_count = 0

pairs_file = open(os.path.join(os.pardir, "data", "pairs.pkl"), 'rb')
pairs = pickle.load(pairs_file)
pairs_file.close()

synonyms_file = open(os.path.join(os.pardir, "data", "synonyms.pkl"), 'rb')
synonyms = pickle.load(synonyms_file)
synonyms_file.close()

connection = pymysql.connect(host='localhost',
                             user='root',
                             password='{}'.format(sys.argv[1]),
                             db='stackoverflow')


start = 0
end = 10000


def contains_key_tech(words):
    for key in pairs.keys():
        if key in words:
            for value in pairs[key]:
                if value in words:
                    return True
    return False


def contains_tech(tech, line, words):
    if " " in tech:
        return tech in line
    else:
        return tech in words

def check_tech_pairs(words):
    line = " ".join(words)
    for first in pairs.keys():
        for first_tech in synonyms[first]:
            if contains_tech(first_tech, line, words):
                for second in pairs[first]:
                    for second_tech in synonyms[second]:
                        if contains_tech(second_tech, line, words):
                            line = line.replace(first_tech, first)
                            line = line.replace(second_tech, second)
                            return (line, first, second)
    return None


try:
    with connection.cursor() as cursor:
        sql = "SELECT Id, Body FROM Posts WHERE Score >= 0 AND Id >= {} AND Id < {}".format(start, end)
        cursor.execute(sql)
        for i in range(cursor.rowcount):
            post_count += 1
            current_id, row = cursor.fetchone()
            word_list = get_words(row)
            total_sent_count += len(word_list)

            for words in word_list:
                rtn = check_tech_pairs(words)
                if rtn is not None:
                    compa_sent_count += 1
                    data_file = open(os.path.join(os.pardir, "out", "tech_v2", "tech_sentences.txt"), "a")
                    data_file.write("{}\n".format(current_id))
                    data_file.write("{}\t{}\n".format(rtn[1], rtn[2]))
                    data_file.write("{}\n".format(rtn[0]))
                    data_file.write("\n")
                    data_file.close()

            # for words in word_list:
            #     if contains_key_tech(words):
            #         compa_sent_count += 1
            #         data_file = open(os.path.join(os.pardir, "data", "key_tech", "key_tech_sentences-v2.txt"), "a")
            #         data_file.write("{}\n".format(current_id))
            #         data_file.write(" ".join(words))
            #         data_file.write("\n")
            #         data_file.close()

finally:
    end_time = time.time()
    summary_file = open(os.path.join(os.pardir, "out", "tech_v2", "tech_summary.txt"), "a")
    summary_file.write("Id from {} to {} in {}\n".format(start, current_id, end_time-start_time))
    summary_file.write("Comparative sentences: {}\n".format(compa_sent_count))
    summary_file.write("Sentence number: {}\n".format(total_sent_count))
    summary_file.write("Post number: {}\n".format(post_count))
    summary_file.write("\n")
    summary_file.close()
    connection.close()
