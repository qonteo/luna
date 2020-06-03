class ExtractPolicy:
    """
       Handler policy.This policy regulates how an input image will be extracted.

       Attributes:
           estimate_quality (int):  estimate or not the image quality.
           estimate_attributes (int):  estimate or not the faces' attributes.
           score_threshold (int):  reject all faces with the quality lower than this value.
       """
    def __init__(self, **kwargs):
        self.estimate_quality = 0
        self.estimate_attributes = 0
        self.score_threshold = 0
        # self.extract_exif = False

        for member in self.__dict__:
            if member in kwargs:
                self.__dict__[member] = kwargs[member]

    def __repr__(self):
        return str(self.__dict__)

    def dict(self):
        """
        Return dict with the Luna API extract request parameters.

        :rtype: dict
        :return:    {
                    "estimateQuality": self.estimate_quality,
                    "scoreThreshold": self.score_threshold,
                    "estimateAttributes": self.estimate_attributes
                    }

        """
        return {"estimateQuality": self.estimate_quality,
                "scoreThreshold": self.score_threshold,
                "estimateAttributes": self.estimate_attributes}

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__