import os
import pyodbc
from Utils import get_db_base_path
import logging
from Logger import get_logger, clean_log_files

def connect_database(logger:logging.Logger, mdb_file_name:str)->tuple[pyodbc.Connection, pyodbc.Cursor]:
    # Get mdb file path
    # base_path = get_current_dir_path()
    base_path = get_db_base_path(logger)
    if not base_path:
        return None, None
    mdb_file = os.path.join(base_path, mdb_file_name)
    logger.info("MDB file path:\n{}".format(mdb_file))

    if not os.path.exists(mdb_file):
        logger.error("MDB file not exist")
        return None, None

    driver = "{Microsoft Access Driver (*.mdb, *.accdb)}"
    conn = pyodbc.connect(f"driver={driver};DBQ={mdb_file}")
    cursor = conn.cursor()
    return conn, cursor


def disconnect_database(conn:pyodbc.Connection, cursor:pyodbc.Cursor):
    cursor.close()
    conn.close()
    return


def set_project_path(project_id:int, project_path:str, logger:logging.Logger,
                     mdb_file_name:str="caseManage .mdb")->str:
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return False

    sql = "UPDATE ProjectInformation SET ProjectPath='{}' WHERE ID={}".format(project_path, project_id)
    try:
        cursor.execute(sql)
    except:
        logger.error("Set project path error, SQL:{}".format(sql))
        disconnect_database(conn=conn, cursor=cursor)
        return False

    conn.commit()
    return True


def get_project_path(project_id:int, logger:logging.Logger, mdb_file_name:str="caseManage .mdb")->str:
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return None

    sql = "SELECT ProjectPath FROM ProjectInformation WHERE ID={}".format(project_id)
    try:
        cursor.execute(sql)
    except:
        logger.error("Get project path, SQL excute error. sql:{}".format(sql))
        disconnect_database(conn=conn, cursor=cursor)
        return None

    rows = cursor.fetchall()
    if len(rows) != 1:
        logger.error("Get project path error, result number:{}".format(len(rows)))
        disconnect_database(conn=conn, cursor=cursor)
        return None
    project_path = rows[0][0]

    disconnect_database(conn=conn, cursor=cursor)
    return project_path


def get_ide_path(project_id:str, logger: logging.Logger, mdb_file_name:str="caseManage .mdb")->str:
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return None

    sql = "SELECT idePath FROM ProjectInformation WHERE ID={}".format(project_id)
    try:
        cursor.execute(sql)
    except:
        logger.error("Get IDE path error, result number:{}".format(len(rows)))
        disconnect_database(conn=conn, cursor=cursor)
        return None

    rows = cursor.fetchall()
    if len(rows) != 1:
        logger.error("Get IDE path error, result number:{}".format(len(rows)))
        disconnect_database(conn=conn, cursor=cursor)
        return None
    ide_path = rows[0][0]

    disconnect_database(conn=conn, cursor=cursor)
    return ide_path


def get_project_name(project_id:int, logger:logging.Logger, mdb_file_name="caseManage .mdb")->str:
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return None

    sql = "SELECT ProjectName FROM ProjectInformation WHERE ID={}".format(project_id)
    try:
        cursor.execute(sql)
    except:
        logger.error("Get project name error, SQL:{}".format(sql))
        disconnect_database(conn=conn, cursor=cursor)
        return None

    rows = cursor.fetchall()
    if len(rows) != 1:
        logger.error("Get project name error, get item: {}".format(len(rows)))
        disconnect_database(conn=conn, cursor=cursor)
        return None

    project_name = rows[0][0]
    disconnect_database(conn=conn, cursor=cursor)
    return project_name


def get_count_by_name(project_name:str, logger:logging.Logger, mdb_file_name="caseManage .mdb")->int:
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return None

    sql = "SELECT COUNT(*) FROM ProjectInformation WHERE ProjectName='{}'".format(project_name)
    try:
        cursor.execute(sql)
    except:
        logger.error("Get project name error, SQL:{}".format(sql))
        disconnect_database(conn=conn, cursor=cursor)
        return None

    data = cursor.fetchone()
    if len(data) != 1:
        logger.error("Get project name error, get item: {}".format(len(data)))
        disconnect_database(conn=conn, cursor=cursor)
        return None

    count = data[0]
    disconnect_database(conn=conn, cursor=cursor)
    return count


def get_code_source(project_id:int, logger:logging.Logger, mdb_file_name:str="caseManage .mdb")->str:
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return None

    sql = "SELECT SourcePath FROM ProjectInformation WHERE ID={}".format(project_id)
    try:
        cursor.execute(sql)
    except:
        logger.error("Get code source error, SQL:{}".format(sql))
        disconnect_database(conn=conn, cursor=cursor)
        return None

    rows = cursor.fetchall()
    if len(rows) != 1:
        logger.error("Get code source error, get item: {}".format(len(rows)))
        disconnect_database(conn=conn, cursor=cursor)
        return None

    code_source = rows[0][0]
    disconnect_database(conn=conn, cursor=cursor)
    return code_source


def get_node_name(project_id:int, module_id:str, sub_id:str, logger:logging.Logger, mdb_file_name:str="caseManage .mdb")->str:
    project_name = get_project_name(project_id=project_id, logger=logger)
    if not project_name:
        logger.error("Get project_name error, project_id={}".format(project_id))
        return None
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return None

    sql = "SELECT NodName FROM TestCase WHERE ModuleID='{}' and SubID='{}'".format(module_id, sub_id)
    try:
        cursor.execute(sql)
    except:
        logger.error("Execute SQL error, sql={}".format(sql))
        disconnect_database(conn=conn, cursor=cursor)
        return None
    rows = cursor.fetchall()
    if len(rows) != 1:
        logger.error("Get node name error, get item: {}".format(len(rows)))
        disconnect_database(conn=conn, cursor=cursor)
        return None

    node_name = rows[0][0]
    disconnect_database(conn=conn, cursor=cursor)
    return node_name


#-------------------------------------------- Test function ------------------------------------------------#
def add_new_colum(table_name:str, colum_name:str, colum_type:str,
                  logger:logging.Logger, mdb_file_name:str="caseManage .mdb")->bool:
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return False

    sql = "ALTER TABLE {} ADD COLUMN {} {};".format(table_name, colum_name, colum_type)
    try:
        cursor.execute(sql)
        conn.commit()
    except:
        logger.error("SQL execute error. SQL:{}".format(sql))
        disconnect_database(conn=conn, cursor=cursor)
        return False

    disconnect_database(conn=conn, cursor=cursor)
    return True


def get_colums_name(table_name:str, logger:logging.Logger, mdb_file_name:str="caseManage .mdb") -> list:
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return None

    try:
        columns = cursor.columns(table=table_name)
    except:
        logger.error("Get columns error.")
        disconnect_database(conn=conn, cursor=cursor)
        return None

    columns_name = []
    for column in columns:
        columns_name.append(column.column_name)

    disconnect_database(conn=conn, cursor=cursor)
    return columns_name


def show_table_column(table_name:str, logger:logging.Logger):
    columns_name = get_colums_name(table_name=table_name, logger=logger)
    print("TableName:{}".format(table_name))
    for column_name in columns_name:
        print("\tColumnName:*{}*".format(column_name))
    return


'''
def add_new_line_for_project_info(mdb_file_name:str="caseManage .mdb"):
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return False

    sql = "INSERT INTO ProjectInformation "\
          "(ID, ProjectName, ProjectPath, EwpPath, CoreArch, Compiler, DownLoader, SourcePath, idePath)" \
          "VALUES" \
          "(5, 'slt_test', 'F:\\Work\\IAR_WorkSpace\\emps_SLT_demo_20240402', '', '', '', '', '', 'F:\\Programs\\IAR Systems\\Embedded Workbench 9.2')"
    logger.info("SQL:\n\t{}".format(sql))
    try:
        cursor.execute(sql)
        conn.commit()
    except:
        logger.error("SQL execute error.")
        disconnect_database(conn=conn, cursor=cursor)
        return False

    disconnect_database(conn=conn, cursor=cursor)
    return True
# '''


def add_item_for_project_info(project_id:int,
                              project_name:str,
                              project_path:str,
                              source_path:str,
                              ide_path:str,
                              logger:logging.Logger,
                              mdb_file_name:str="caseManage .mdb"):
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return False

    sql = "SELECT * FROM ProjectInformation WHERE ID={}".format(project_id)
    logger.info("SQL:\n\t{}".format(sql))
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
    except:
        logger.error("SQL execution error, SQL={}".format(sql))
        disconnect_database(conn=conn, cursor=cursor)
        return False
    if len(rows) != 0:
        logger.info("Item already exists, no need add, project_id={}".format(project_id))
        return True

    sql = "INSERT INTO ProjectInformation "\
          "(ID, ProjectName, ProjectPath, EwpPath, CoreArch, Compiler, DownLoader, SourcePath, TestType, idePath)" \
          "VALUES" \
          "({}, '{}', '{}', '', '', '', '', '{}', '', '{}')".format(project_id, project_name, project_path, source_path, ide_path)
    logger.info("SQL:\n\t{}".format(sql))
    try:
        cursor.execute(sql)
        conn.commit()
    except:
        logger.error("SQL execute error.")
        disconnect_database(conn=conn, cursor=cursor)
        return False

    disconnect_database(conn=conn, cursor=cursor)
    return True


def del_item_from_table(project_id:int, table_name:str, logger:logging.Logger,
                        mdb_file_name="caseManage .mdb")->bool:
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return False

    sql = "DELETE FROM {} WHERE ID={}".format(table_name, project_id)
    try:
        cursor.execute(sql)
        conn.commit()
    except:
        logger.error("SQL execute error, SQL:{}".format(sql))
        disconnect_database(conn=conn, cursor=cursor)
        return False

    disconnect_database(conn=conn, cursor=cursor)
    return True


def show_table_info_table(table_name:str, mdb_file_name:str="caseManage .mdb"):
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return False

    sql="SELECT * FROM {}".format(table_name)
    try:
        cursor.execute(sql)
    except:
        logger.error("SQL executes error, SQL:{}".format(sql))
        disconnect_database(conn=conn, cursor=cursor)
        return False

    rows = cursor.fetchall()
    for row in rows:
        print(row)

    disconnect_database(conn=conn, cursor=cursor)
    return True

def update_code_source(project_id:int, code_source:str, mdb_file_name:str="caseManage .mdb")->bool:
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return False

    sql="UPDATE ProjectInformation SET SourcePath='{}' WHERE ID={}".format(code_source, project_id)
    try:
        cursor.execute(sql)
    except:
        logger.error("Update code source error, SQL:{}".format(sql))
        disconnect_database(conn=conn, cursor=cursor)
        return False
    conn.commit()

    disconnect_database(conn=conn, cursor=cursor)
    return True


if __name__ == "__main__":
    clean_log_files()
    logger = get_logger("DBA_Log")
    # table_name = "ProjectInformation"
    table_name = "TestCase"
    show_table_info_table(table_name=table_name)
    show_table_column(table_name=table_name, logger=logger)
    # count = get_count_by_name(project_name="GitTest", logger=logger)
    # print("Rows Type: {}".format(type(count)))
    # print("Rows:\n\t{}".format(count))
    node_name = get_node_name(project_id=1, module_id="MODULE_ID_CMU", sub_id="0x0001", logger=logger)
    print("node_name = {}".format(node_name))