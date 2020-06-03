

class AdminStats:
    """
    Structure for storing admin stats

    """
    def __init__(self, series, tags = None, values = None):
        """
        Initialization of structrure.

        :param series: name of series
        :param tags: dict of tags
        :param values: dict of values
        """

        self.series = series        #: name of series in influxdb

        self.tags = {}            #: dict of tags in influxdb
        if tags is not None:
            self.tags = tags

        self.values = {}            #: dict of values in influxdb
        if values is not None:
            self.values = values

    def getStrToInfluxRequest(self):
        """
        Generate string for request to influxdb

        :rtype: string
        :return: string in format "series_name,tag1=tag1_value,tag2=tag2_value,..., value1=value1_value"
        """
        influxRequest = self.series
        for tag in self.tags:
            influxRequest += ",{}={}".format(tag, self.tags[tag])
        influxRequest += " "
        for value in self.values:
            influxRequest += "{}={},".format(value, self.values[value])
        influxRequest = influxRequest[:-1]
        return influxRequest

    def update(self, tags = None, values = None):
        """
        Update tags and values

        :param tags: dict for update self.tags
        :param values: dict for update self.values
        :return:
        """
        if tags is not None:
            self.tags.update(tags)
        if values is not None:
            self.values.update(values)
