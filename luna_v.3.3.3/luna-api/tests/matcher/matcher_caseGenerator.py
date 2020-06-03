class CaseGenerator:

    @staticmethod
    def generateCase(queries, msgFormat=None, error=None):
        return {
            "queries": queries,
            "msgFormat": msgFormat,
            "error": error
        }


    @staticmethod
    def badIdQueryParamsTestSuiteIdentifierGenerator(personListId, photoId, badId):
        return (
            CaseGenerator.generateCase(
                {"list_id": personListId, "person_id": badId},
                ["person_id"]
            ),
            CaseGenerator.generateCase(
                {"list_id": personListId, "descriptor_id": badId},
                ["descriptor_id"]
            ),
            CaseGenerator.generateCase(
                {"descriptor_id": photoId, "list_id": badId},
                ["list_id"]
            ),
            CaseGenerator.generateCase(
                {"descriptor_id": photoId, "person_ids": badId},
                ["person_ids"]
            )
        )
    
    @staticmethod
    def badIdQueryParamsTestSuiteMatcherGenerator(descriptorListId, photoId, badId):
        return (
            CaseGenerator.generateCase(
                {"list_id": descriptorListId, "person_id": badId},
                ["person_id"]
            ),
            CaseGenerator.generateCase(
                {"list_id": descriptorListId, "descriptor_id": badId},
                ["descriptor_id"]
            ),
            CaseGenerator.generateCase(
                {"descriptor_id": photoId, "list_id": badId},
                ["list_id"]
            ),
            CaseGenerator.generateCase(
                {"descriptor_id": photoId, "descriptor_ids": badId},
                ["descriptor_ids"]
            )
        )

    @staticmethod
    def badIdQueryParamsTestSuiteSearchGenerator(badId):
        return (
            CaseGenerator.generateCase({"list_id": badId}, ["list_id"]),
            CaseGenerator.generateCase({"person_ids": badId}, ["person_ids"]),
            CaseGenerator.generateCase({"descriptor_ids": badId}, ["descriptor_ids"])
        )
    
    @staticmethod
    def badIdQueryParamsTestSuiteVerifyGenerator(badId, photoId, personId):
        return (
            CaseGenerator.generateCase({"person_id": badId, "descriptor_id": photoId}, ["person_id"]),
            CaseGenerator.generateCase({"descriptor_id": badId, "person_id": personId}, ["descriptor_id"])
        )
