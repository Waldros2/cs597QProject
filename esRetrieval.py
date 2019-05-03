import datetime
import csv
from collections import defaultdict
from elasticsearch import Elasticsearch

#Establish date range
index = 'logstash-2018.04.30'
date = datetime.datetime(2018, 4, 30)

#Establish ElasticSearch
es = Elasticsearch()

#Establish indices for the days
indices = []
for i in range(31):
    indices.append('logstash-' + date.strftime('%Y.%m.%d'))
    date += datetime.timedelta(days=1)

#Collect from days
for index in indices:
    print('Collecting from ' + index)
    byteFlow = defaultdict(float)
    try:
        res = es.search(index=index, q='clientID : washougal AND _type: netflow', size=10000, scroll='1m')
        while len(res['hits']['hits']) > 0:
            for hit in res['hits']['hits']:
                netflow = hit['_source']['netflow']
                
                #Establish src/dst
                if('192.168' not in netflow['ipv4_src_addr']):
                    src = 'superNode'
                else:
                    src = netflow['ipv4_src_addr']
                    
                if('192.168' not in netflow['ipv4_dst_addr']):
                    dst = 'superNode'
                else:
                    dst = netflow['ipv4_dst_addr']
                
                byteFlow[(src,dst)] += (netflow['out_bytes'] / 2**20)
                byteFlow[(dst,src)] += (netflow['in_bytes'] / 2**20)
                
            scroll = res['_scroll_id']
            res = es.scroll(scroll_id=scroll, scroll='1m')
        with open('../data/byte/byte_' + index + '.csv', 'w') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(['src','dst','MB'])
            for key, value in byteFlow.items():
                writer.writerow([key[0], key[1], value])

    except Exception as e:
        print('Could not collect from ' + index)
        print(e)

