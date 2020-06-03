if __name__ == '__main__':
    from requests import get, delete, put
    from common.elasticsearch.index import indexes
    from configs.config import ELASTICSEARCH_URL as es_url

    overwrite = False
    for index in indexes:
        reply = get(es_url + index[0])
        if reply.status_code == 200:
            if not overwrite and input('Overwrite index on "{}"? [y/n]\n'.format(es_url)) not in 'yesYES':
                print('Canceled')
                exit()
            overwrite = True
            reply = delete(es_url + index[0])
        if reply.status_code == 200:
            print('Removed index "{}"'.format(index[0]))
        else:
            print('Did not exist index "{}"'.format(index[0]))
        reply = put(es_url + index[0], json=index[1])
        if reply.status_code == 200:
            print('Created index "{}"'.format(index[0]))
        else:
            raise ValueError('Index create reply is\n{}:\n{}'.format(reply.status_code, reply.text))
