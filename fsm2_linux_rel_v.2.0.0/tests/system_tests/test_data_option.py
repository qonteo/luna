from uuid import uuid4

personsImgs = [
    ["./data/girl_1_0.jpg", "./data/girl_1_1.jpg"],
    ["./data/girl_2_0.jpg", "./data/girl_2_1.jpg"],
    ["./data/man_1_0.jpg", "./data/man_1_1.jpg"]
]

events = [
    "./data/girl_1_0.jpg",
    "./data/girl_2_0.jpg",
    "./data/man_1_0.jpg",
]

descriptorsImgs = ["./data/girl_1_1.jpg",
                   "./data/girl_2_1.jpg",
                   "./data/man_1_1.jpg"]

simEvents = ["./data/man_young.jpg"]

uuid = str(uuid4())

neededFields = {
    'aggregator': 'count',
    'group_by': '1d',
}

personsImgs_search = ["./data/girl_1_0.jpg",
                      "./data/girl_2_0.jpg",
                      "./data/man_1_0.jpg"]
descriptorsImgs_search = ["./data/girl_1_1.jpg",
                          "./data/girl_2_1.jpg",
                          "./data/man_1_1.jpg"]
events_search = ["./data/man_1_1.jpg"]

additional_fields = (
    '',
    "search_policy.search_lists.0",
    "search_policy",
    "grouping_policy.create_person_policy.create_filters.age_range",
    "grouping_policy.create_person_policy.create_filters.similarity_filter.lists.0",
    "grouping_policy.create_person_policy.create_filters.similarity_filter",
    "grouping_policy.create_person_policy.create_filters",
    "grouping_policy.create_person_policy",
    "grouping_policy.create_person_policy.attach_policy.0.filters.age_range",
    "grouping_policy.create_person_policy.attach_policy.0.filters.similarity_filter.lists.0",
    "grouping_policy.create_person_policy.attach_policy.0.filters.similarity_filter",
    "grouping_policy.create_person_policy.attach_policy.0.filters",
    "grouping_policy.create_person_policy.attach_policy.0",
    "grouping_policy",
    "descriptor_policy.attach_policy.0.filters.age_range",
    "descriptor_policy.attach_policy.0.filters.similarity_filter.lists.0",
    "descriptor_policy.attach_policy.0.filters.similarity_filter",
    "descriptor_policy.attach_policy.0.filters",
    "descriptor_policy.attach_policy.0",
    "descriptor_policy",
    "extract_policy",
    "person_policy.create_person_policy.create_filters.age_range",
    "person_policy.create_person_policy.create_filters.similarity_filter.lists.0",
    "person_policy.create_person_policy.create_filters.similarity_filter",
    "person_policy.create_person_policy.create_filters",
    "person_policy.create_person_policy",
    "person_policy.create_person_policy.attach_policy.0.filters.age_range",
    "person_policy.create_person_policy.attach_policy.0.filters.similarity_filter.lists.0",
    "person_policy.create_person_policy.attach_policy.0.filters.similarity_filter",
    "person_policy.create_person_policy.attach_policy.0.filters",
    "person_policy.create_person_policy.attach_policy.0",
    "person_policy",
)

cases = {
    'test_group_filter': 'groups',
    'test_group_by_minuteOfDay': 'minuteOfDay',
    'test_group_by_hourOfDay': 'hourOfDay',
    'test_group_by_dayOfWeek': 'dayOfWeek',
    'test_group_by_dayOfMonth': 'dayOfMonth',
    'test_group_by_dayOfYear': 'dayOfYear',
    'test_group_by_monthOfYear': 'monthOfYear',
}
