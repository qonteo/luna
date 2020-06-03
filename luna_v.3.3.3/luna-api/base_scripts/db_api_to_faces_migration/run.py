from functions import counters, MigrateFunctions, skipMigration, cleanFlag, dropOldTables, checkConnection, logger
from functions import migrateAccountsFlag


def migrateTables():
    """
    Migrates tables to new DB
    """
    logger.debug('Migration starts')

    MigrateFunctions.migrateFace()
    MigrateFunctions.migratePerson()
    MigrateFunctions.migrateList()

    MigrateFunctions.migrateLists()


def migrateAccTables():
    """
    Migrate account and account token tables
    """
    MigrateFunctions.migrateAccount()
    MigrateFunctions.migrateAccountToken()


if __name__ == '__main__':
    checkConnection()
    if not skipMigration:
        migrateTables()
    if cleanFlag:
        dropOldTables()
    if migrateAccountsFlag:
        migrateAccTables()
    if not skipMigration or migrateAccountsFlag:
        logger.debug('Migration results:')
        for cntName, cntValue in counters.items():
            logger.debug(' table {}: success {} errors: {}'.format(cntName, cntValue['success'], cntValue['errors']))
