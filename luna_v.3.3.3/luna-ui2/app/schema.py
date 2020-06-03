import graphene
from mutations import Mutations
from queries import Query


Schema = graphene.Schema(query=Query, mutation=Mutations)
