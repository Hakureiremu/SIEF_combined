#This is a script to process the format of my self-established data into that of docRed
import json
import re
import spacy

nlp = spacy.load("en_core_web_sm")
with open('admin.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        for entity in data['entities']:
            entity['name'] = data['text'][entity['start_offset']:entity['end_offset']]
            #print(entity['name'])

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
        for line in str.splitlines():
            if(line):
                sent = []
                doc = nlp(line)
                for token in doc:
                    sent.append(token.text)
                sents.append(sent)  #分词
        data['sents'] = sents

        #按docRed格式获得实体的新表示
        i = 0
        j = 0
        flag = 0
        start_point = 0
        sentence = []
        print("process entity...")
        for entity in data['entities']:
            #print(entity)
            if entity['start_offset'] > delimiter_point: #只取正文中实体
                entity_name = []
                doc = nlp(entity['name'])
                for token in doc:
                    entity_name.append(token.text)
                #print(entity_name)
                #print(entity)
                for i in range(len(sents)):
                    if(flag == 1):
                        flag = 0
                        break
                    #print(sents[i])
                    for j in range(len(sents[i])):
                        if entity_name[0] == sents[i][j]:
                            entity['sent_id'] = i
                            position = []
                            position.append(j)
                            position.append(j+len(entity_name))
                            entity['pos'] = position
                            #print(sents[i])
                            #print(entity['sent_id'])
                            #print(position)
                            flag = 1
                            break
        print("finished")

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
        print(mention_id_set)

        #将无共指的孤立实体加入vertex
        exist_mention_id = [element for sublist in mention_id_set for element in sublist]
        for entity in data['entities']:
            id = entity['id']
            if id not in exist_mention_id:
                mention_id_set.append(id)
        print(mention_id_set)

        #统一合并到新数据格式
        doc_dataset = []
        doc_data = {}
        new_entity = {}
        vertexSet = []
        for mentions in mention_id_set:
            vertex = []
            for id in mentions:
                for entity in data['entities']:
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
                        vertex.append(new_entity)
            vertexSet.append(vertex)
        doc_data['vertexSet'] = vertexSet


        break


