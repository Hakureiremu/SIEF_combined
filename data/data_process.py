#This is a script to process the format of my self-established data into that of docRed
import json
import re
import spacy
import random

doc_dataset = [] #总体数据结构
rand_flg = 0 #随机数种子
nlp = spacy.load("en_core_web_sm") #分词预训练模型
index = 0

with open('admin.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        index += 1
        data = json.loads(line)
        for entity in data['entities']:
            entity['name'] = data['text'][entity['start_offset']:entity['end_offset']]
        #print(data['entities'])

        #先处理text再调整实体
        str = data['text']
        pos = str.find("tweets:")
        str = data['text'][pos+len("tweets:"):]
        delimiter_point = pos + len("tweets:")

        # for entity in data['entities']:
        #     if entity['name'] in str:
        #         entity['start_offset'] -= (pos+len("tweets:"))
        #         entity['end_offset'] -= (pos+len("tweets:"))
        #         #print(entity['name'])
        #         #print(str[entity['start_offset']:entity['end_offset']])
        #str = re.sub(r'[\U0001F600-\U0001F64F]', '', str) #去除网络表情
        pos = str.find("\n")
        str = str[pos+len("\n"):]
        delimiter_point += len("\n")
        #print(delimiter_point)

        #分词，获得句子的新表示
        sents = []
        sents_checklist = []
        sent_split_pos = []
        sent_split = delimiter_point
        #print(str)
        for line in str.splitlines():
            if(line):
                sent = []
                doc = nlp(line)
                sent_split += len(line)
                for token in doc:
                    sent.append(token.text)
                sent_check = [1] * len(sent)
                sent_split_pos.append(sent_split)
                sents.append(sent)  #分词
                sents_checklist.append(sent_check)
                #print(str[0:sent_split-delimiter_point])
            sent_split += len("\n")
        data['sents'] = sents
        #print(sent_split_pos)
        #print(sents)

        #按docRed格式获得实体的新表示
        i = 0
        j = 0
        flag = 0
        sentence = []
        tmp_entity = []
        print("process entity...")

        for entity in data['entities']:
            print(entity)
            if entity['start_offset'] > delimiter_point:
                entity_name = []
                doc = nlp(entity['name'])
                for token in doc:
                    entity_name.append(token.text)
                #print(entity_name)
                for i in range(len(sent_split_pos)):
                    #print(flag)
                    #print(entity['start_offset'])
                    #print(sent_split_pos[i])
                    if flag == 1:
                        flag = 0
                        break
                    if entity['start_offset'] < sent_split_pos[i]:
                        entity['sent_id'] = i
                        #print(sents[i])
                        for j in range(len(sents[i])):
                            if entity_name[:-1] == sents[i][j:j + len(entity_name)] and sents_checklist[i][j]:
                                #print("find! ", entity_name)
                                entity['sent_id'] = i
                                position = []
                                position.append(j)
                                position.append(j + len(entity_name))
                                entity['pos'] = position
                                tmp_entity.append(entity)
                                sents_checklist[i][j:j + len(entity_name) - 1] = [0] * (len(entity_name) - 1)
                                flag = 1
                                break
                    if i == len(sent_split_pos)-1:
                        flag = 0

        # for entity in data['entities']:
        #     #print(entity)
        #     if entity['start_offset'] > delimiter_point: #只取正文中实体
        #         entity_name = []
        #         doc = nlp(entity['name'])
        #         for token in doc:
        #             entity_name.append(token.text)
        #         print(entity_name)
        #         #print(entity)
        #         for i in range(len(sents)):
        #             if(flag == 1):
        #                 flag = 0
        #                 break
        #             #print(sents[i])
        #             for j in range(len(sents[i])):
        #                 if entity_name[0] == sents[i][j] and entity_name[len(entity_name)-1] == sents[i][j+len(entity_name)-1] and sents_checklist[i][j]:
        #                     print("find! ", entity_name)
        #                     entity['sent_id'] = i
        #                     position = []
        #                     position.append(j)
        #                     position.append(j+len(entity_name))
        #                     entity['pos'] = position
        #                     tmp_entity.append(entity)
        #                     sents_checklist[i][j:j+len(entity_name)-1] = [0] * (len(entity_name)-1)
        #                     flag = 1
        #                     break
        # for entity in tmp_entity:
        #     print(entity['pos'])
        #print(tmp_entity)
        #print(len(tmp_entity))
        #print(len(data['entities']))


        #聚合共指
        j = 0
        stk = []
        ent_checklist = [1] * len(data['entities'])
        mention_id_set = []
        #relations = sorted(data['relations'], key=lambda x: x['from_id'])
        #先统计共指
        con_relations = []
        for relation in data['relations']:
            if relation['type'] == "共指":
                con_relations.append(relation)
        #print(con_relations)

        rel_checklist = [1] * len(con_relations)
        for i in range(len(con_relations)):
            if rel_checklist[i]:
                mention_id = []
                relation = con_relations[i]
                mention_id.append(relation['from_id'])
                mention_id.append(relation['to_id'])
                j = i + 1
                while j in range(len(con_relations)) and rel_checklist[j]:
                    if con_relations[j]['from_id'] in mention_id or con_relations[j]['to_id'] in mention_id:
                        rel_checklist[j] = 0
                        mention_id.append(con_relations[j]['from_id'])
                        mention_id.append(con_relations[j]['to_id'])
                    j+=1
                mention_id_set.append(list(sorted(set(mention_id))))
        #print(mention_id_set)

        #将无共指的孤立实体加入vertex
        exist_mention_id = [element for sublist in mention_id_set for element in sublist]
        #print(exist_mention_id)
        for entity in tmp_entity:
            id = []
            id.append(entity['id'])
            if entity['id'] not in exist_mention_id and entity['start_offset'] > delimiter_point and entity['label'] != "无法判定":
                mention_id_set.append(id)
        #print(mention_id_set)

        # id_set = []
        # for entity in tmp_entity:
        #     id_set.append(entity['id'])
        # print(id_set)
        #
        # for id in id_set:
        #     for mentions in mention_id_set:
        #         if id in mentions:
        #             break
        #     print(id)
        # break

        #统一合并到新数据格式

        doc_data = {}
        vertexSet = []
        for mentions in mention_id_set:
            vertex = []
            #print(mentions)
            for id in mentions:
                #print(mentions)
                for entity in tmp_entity:
                    #print(entity)
                    new_entity = {}
                    if id == entity['id']:
                        new_entity['name'] = entity['name']
                        new_entity['pos'] = entity['pos']
                        new_entity['sent_id'] = entity['sent_id']
                        if entity['label'] == "国家":
                            new_entity['type'] = "NATION"
                        elif entity['label'] == "组织":
                            new_entity['type'] = "ORGANIZATION"
                        elif entity['label'] == "城市":
                            new_entity['type'] = "CITY"
                        elif entity['label'] == "人物":
                            new_entity['type'] = "PERSON"
                        elif entity['label'] == "抽象类":
                            new_entity['type'] = "ABSTRACT"
                        elif entity['label'] == "触发词":
                            new_entity['type'] = "TRIGWORD"
                        vertex.append(new_entity)
                        break

            vertexSet.append(vertex)
        doc_data['vertexSet'] = vertexSet
        #print(vertexSet)
        #break

        #根据mention id建一个sentence表
        id_check_list = []
        for mentions in mention_id_set:
            for id in mentions:
                id_check_list.append(id)

        #处理关系并转换为新格式
        labels = []
        for relation in data['relations']:
            rel = {}
            evidence = []
            if relation['from_id'] not in id_check_list:
                continue

            if relation['type'] == "共指":
                continue
            if relation['type'] == "所属":
                rel['r'] = "P1"
            if relation['type'] == "支持":
                rel['r'] = "P2"
            if relation['type'] == "反对":
                rel['r'] = "P3"
            if relation['type'] == "推进":
                rel['r'] = "P4"
            if relation['type'] == "遏制":
                rel['r'] = "P5"
            if relation['type'] == "知道":
                rel['r'] = "P6"
            if relation['type'] == "触发":
                rel['r'] = "P7"

            #print(relation)

            for i in range(len(mention_id_set)):
                if relation['from_id'] in mention_id_set[i]:
                    rel['h'] = i
                    break
            for j in range(len(mention_id_set)):
                if relation['to_id'] in mention_id_set[j]:
                    rel['t'] = i
                    break

            #找evidence句
            for entity in tmp_entity:
                if relation['from_id'] == entity['id'] and entity['sent_id'] not in evidence:
                    evidence.append(entity['sent_id'])
                if relation['to_id'] == entity['id'] and entity['sent_id'] not in evidence:
                    evidence.append(entity['sent_id'])

            #将共指关系间的句子按随机因子纳入支持性证据
            random.seed(++rand_flg)
            select_choice = random.randint(1,3)
            if select_choice == 2:
                random.seed(++rand_flg)
                add_index = random.randint(0,len(mention_id_set[rel['h']])-1)
                for entity in tmp_entity:
                    if entity['id']==mention_id_set[rel['h']][add_index] and entity['sent_id'] not in evidence:
                        evidence.append(entity['sent_id'])
            if select_choice == 3:
                random.seed(++rand_flg)
                add_index = random.randint(0, len(mention_id_set[rel['t']]) - 1)
                for entity in tmp_entity:
                    if entity['id'] == mention_id_set[rel['t']][add_index] and entity['sent_id'] not in evidence:
                        evidence.append(entity['sent_id'])

            rel['evidence'] = sorted(evidence)
            if rel not in labels:
                labels.append(rel)

        print("finished ", index)
        #print(labels)
        doc_data['labels'] = labels
        #print(sents)
        doc_data['sents'] = sents
        print(doc_data)
        doc_dataset.append(doc_data)



