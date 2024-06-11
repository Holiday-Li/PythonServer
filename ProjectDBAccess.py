import os
import pyodbc
from Utils import get_current_dir_path
import logging
from Logger import get_logger

def connect_database(logger:logging.Logger, mdb_file_name:str)->tuple[pyodbc.Connection, pyodbc.Cursor]:
    # Get mdb file path
    base_path = get_current_dir_path()
    mdb_file = os.path.join(base_path, mdb_file_name)
    logger.info("MDB file path:\n{}".format(mdb_file))

    if not os.path.exists(mdb_file):
        logger.error("MDB file not exist")
        return None, None

    driver = "{Microsoft Access Driver (*.mdb, *.accdb)}"
    conn = pyodbc.connect(f"driver={driver};DBQ={mdb_file}")
    cursor = conn.cursor()
    return conn, cursor


def close_database(conn:pyodbc.Connection, cursor:pyodbc.Cursor):
    cursor.close()
    conn.close()
    return


def get_project_path(project_id:int, logger:logging.Logger, mdb_file_name:str="caseManage .mdb")->str:
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return None

    sql = "SELECT ProjectPath FROM ProjectInformation WHERE ID={}".format(project_id)
    try:
        cursor.execute(sql)
    except:
        logger.error("Get project path, SQL excute error.")
        close_database(conn=conn, cursor=cursor)
        return None

    rows = cursor.fetchall()
    if len(rows) != 1:
        logger.error("Get project path error, result number:{}".format(len(rows)))
        close_database(conn=conn, cursor=cursor)
        return None
    project_path = rows[0][0]

    close_database(conn=conn, cursor=cursor)
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
        close_database(conn=conn, cursor=cursor)
        return None

    rows = cursor.fetchall()
    if len(rows) != 1:
        logger.error("Get IDE path error, result number:{}".format(len(rows)))
        close_database(conn=conn, cursor=cursor)
        return None
    ide_path = rows[0][0]

    close_database(conn=conn, cursor=cursor)
    return ide_path



def add_new_colum(table_name:str, colum_name:str, colum_type:str,
                  logger:logging.Logger, mdb_file_name:str="caseManage .mdb")->bool:
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return False

    sql = "ALTER TABLE {} ADD COLUMN {} {};".format(table_name, colum_name, colum_type)
    try:
        cursor.execute(sql=sql)
        conn.commit()
    except:
        logger.error("SQL execute error. SQL:{}".format(sql))
        close_database(conn=conn, cursor=cursor)
        return False

    close_database(conn=conn, cursor=cursor)
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
        close_database(conn=conn, cursor=cursor)
        return None

    columns_name = []
    for column in columns:
        columns_name.append(column.column_name)

    close_database(conn=conn, cursor=cursor)
    return columns_name


def show_table_column(table_name:str, logger:logging.Logger):
    columns_name = get_colums_name(table_name=table_name, logger=logger)
    print("TableName:{}".format(table_name))
    for column_name in columns_name:
        print("\tColumnName:{}".format(column_name))
    return


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
        close_database(conn=conn, cursor=cursor)
        return False

    close_database(conn=conn, cursor=cursor)
    return True


def show_table_info_table(table_name:str, mdb_file_name:str="caseManage .mdb"):
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return False

    sql="SELECT * FROM {}".format(table_name)
    try:
        cursor.execute(sql=sql)
    except:
        logger.error("SQL executes error, SQL:{}".format(sql))
        close_database(conn=conn, cursor=cursor)
        return False

    rows = cursor.fetchall()
    for row in rows:
        print(row)

    close_database(conn=conn, cursor=cursor)
    return True


def get_node_name(module_id:str, sub_id:str, logger:logging.Logger, mdb_file_name:str="caseManage .mdb")->str:
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return None

    sql = "SELECT NodName FROM TestCase WHERE MoubleID=? and SubID=?"
    try:
        cursor.execute(sql, (module_id, sub_id))
    except:
        logger.error("Execute SQL error")
        close_database(conn=conn, cursor=cursor)
        return None
    rows = cursor.fetchall()
    if len(rows) != 1:
        logger.error("Get node name error, get item: {}".format(len(rows)))
        close_database(conn=conn, cursor=cursor)
        return None

    node_name = rows[0][0]
    close_database(conn=conn, cursor=cursor)
    return node_name


if __name__ == "__main__":
    logger = get_logger("mdb_test")
    # '''
    table_name = "ProjectInformation"
    print("------------{} Test------------".format(table_name))
    show_table_column(table_name=table_name, logger=logger)
    # add_new_line_for_project_info()
    # show_table_info_table(table_name=table_name)
    print("Test: get_project_path")
    project_path = get_project_path(project_id=5, logger=logger)
    print("\tProjectPath: {}".format(project_path))
    print("\tProjectPathType: {}".format(type(project_path)))
    print("Test: get_ide_path")
    ide_path = get_ide_path(project_id=5, logger=logger)
    print("\tidePath: {}".format(ide_path))
    print("\tidePathType: {}".format(type(ide_path)))
    # '''

    table_name = "TestCase"
    print("------------{} Test------------".format(table_name))
    show_table_column(table_name=table_name, logger=logger)
    # show_table_info_table(table_name=table_name)
    print("Get node name:")
    node_name = get_node_name(module_id="MODULE_ID_SPI", sub_id="0x0001", logger=logger)
    print("\tNodeName:{}".format(node_name))
    del logger