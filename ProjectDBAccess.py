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
    try:
        conn = pyodbc.connect(f"driver={driver};DBQ={mdb_file}")
    except:
        logger.error("Database connect error.")
        return None, None
    try:
        cursor = conn.cursor()
    except:
        logger.error("Get cursor error.")
        conn.close()
        return None, None
    return conn, cursor


def disconnect_database(conn:pyodbc.Connection, cursor:pyodbc.Cursor, logger:logging.Logger):
    cursor_close = False
    while True:
        if cursor_close == False:
            try:
                cursor.close()
            except:
                logger.error("Cursor close error.")
                continue
            cursor_close = True
        try:
            conn.close()
        except:
            logger.error("Conn close error.")
            continue
        break
    logger.info("Disconnect database connection.")
    return


def get_count_by_name(project_name:str, logger:logging.Logger, mdb_file_name="caseManage.mdb")->int:
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return None

    sql = "SELECT COUNT(*) FROM ProjectInformation WHERE ProjectName='{}'".format(project_name)
    try:
        cursor.execute(sql)
    except:
        logger.error("Get project name error, SQL:{}".format(sql))
        disconnect_database(conn=conn, cursor=cursor, logger=logger)
        return None

    data = cursor.fetchone()
    if len(data) != 1:
        logger.error("Get project name error, get item: {}".format(len(data)))
        disconnect_database(conn=conn, cursor=cursor, logger=logger)
        return None

    count = data[0]
    disconnect_database(conn=conn, cursor=cursor, logger=logger)
    return count


#-------------------------------------------- Test function ------------------------------------------------#
def add_new_colum(table_name:str, colum_name:str, colum_type:str,
                  logger:logging.Logger, mdb_file_name:str="caseManage.mdb")->bool:
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
        disconnect_database(conn=conn, cursor=cursor, logger=logger)
        return False

    disconnect_database(conn=conn, cursor=cursor, logger=logger)
    return True


def get_colums_info(table_name:str, logger:logging.Logger, mdb_file_name:str="caseManage.mdb") -> list:
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return None

    try:
        columns = cursor.columns(table=table_name)
    except:
        logger.error("Get columns error.")
        disconnect_database(conn=conn, cursor=cursor, logger=logger)
        return None

    columns_info = []
    for column in columns:
        column_info = {
            "name": column.column_name,
            "type": column.type_name,
        }
        # columns_name.append(column.column_name)
        columns_info.append(column_info)

    disconnect_database(conn=conn, cursor=cursor, logger=logger)
    return columns_info


def show_table_column(table_name:str, logger:logging.Logger):
    columns_info = get_colums_info(table_name=table_name, logger=logger)
    print("TableName:{}".format(table_name))
    for column_info in columns_info:
        print("\tColumnName:*{}* - type:*{}*".format(column_info["name"], column_info["type"]))
    return


'''
def add_new_line_for_project_info(mdb_file_name:str="caseManage.mdb"):
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
                              mdb_file_name:str="caseManage.mdb"):
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
        disconnect_database(conn=conn, cursor=cursor, logger=logger)
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
        disconnect_database(conn=conn, cursor=cursor, logger=logger)
        return False

    disconnect_database(conn=conn, cursor=cursor, logger=logger)
    return True


def del_item_from_table(project_id:int, table_name:str, logger:logging.Logger,
                        mdb_file_name="caseManage.mdb")->bool:
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
        disconnect_database(conn=conn, cursor=cursor, logger=logger)
        return False

    disconnect_database(conn=conn, cursor=cursor, logger=logger)
    return True


def show_table_info_table(table_name:str, mdb_file_name:str="caseManage.mdb"):
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return False

    sql="SELECT * FROM {}".format(table_name)
    try:
        cursor.execute(sql)
    except:
        logger.error("SQL executes error, SQL:{}".format(sql))
        disconnect_database(conn=conn, cursor=cursor, logger=logger)
        return False

    rows = cursor.fetchall()
    for row in rows:
        print(row)

    disconnect_database(conn=conn, cursor=cursor, logger=logger)
    return True


def update_item_value(table_name:str,
                      base_key:str,
                      base_value,
                      target_key:str,
                      target_value:str,
                      logger:logging.Logger,
                      mdb_file_name:str="caseManage.mdb")->bool:
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return False

    if isinstance(base_value, str):
        sql="UPDATE {table_name} SET {target_key}='{target_value}' WHERE {base_key}='{base_value}'".format(
            table_name=table_name, target_key=target_key, target_value=target_value, base_key=base_key, base_value=base_value)
    else:
        sql="UPDATE {table_name} SET {target_key}='{target_value}' WHERE {base_key}={base_value}".format(
            table_name=table_name, target_key=target_key, target_value=target_value, base_key=base_key, base_value=base_value)
    try:
        cursor.execute(sql)
    except:
        logger.error("Update code source error, SQL:{}".format(sql))
        disconnect_database(conn=conn, cursor=cursor, logger=logger)
        return False
    conn.commit()

    disconnect_database(conn=conn, cursor=cursor, logger=logger)
    return True


def get_item_value(table_name:str, target_key, base_key:str, base_value, logger:logging.Logger, mdb_file_name:str="caseManage.mdb"):
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return None

    if isinstance(base_value, str):
        sql = "SELECT {target_key} FROM {table_name} WHERE {base_key}='{base_value}'".format(
            table_name=table_name, target_key=target_key, base_key=base_key, base_value=base_value
        )
    else:
        sql = "SELECT {target_key} FROM {table_name} WHERE {base_key}={base_value}".format(
            table_name=table_name, target_key=target_key, base_key=base_key, base_value=base_value
        )

    logger.info("SQL:{}".format(sql))
    try:
        cursor.execute(sql)
    except:
        disconnect_database(conn=conn, cursor=cursor, logger=logger)
        return None

    rows = cursor.fetchall()
    if len(rows) != 1:
        logger.error("Get code source error, get item: {}".format(len(rows)))
        disconnect_database(conn=conn, cursor=cursor, logger=logger)
        return None

    target_value = rows[0][0]
    disconnect_database(conn=conn, cursor=cursor, logger=logger)
    logger.info("TargetValue: {}".format(target_value))
    return target_value


def clean_item_value(table_name:str, target_key:str, base_key:str, base_value, logger:logging.Logger, mdb_file_name:str="caseManage.mdb"):
    conn, cursor = connect_database(logger=logger, mdb_file_name=mdb_file_name)
    if not conn or not cursor:
        logger.error("Connect database error")
        return False

    if isinstance(base_value, str):
        sql = "UPDATE {table_name} SET {target_key}=null WHERE {base_key}='{base_value}'".format(
            table_name=table_name, target_key=target_key, base_key=base_key, base_value=base_value
        )
    else:
        sql = "UPDATE {table_name} SET {target_key}=null WHERE {base_key}={base_value}".format(
            table_name=table_name, target_key=target_key, base_key=base_key, base_value=base_value
        )
    try:
        cursor.execute(sql)
    except:
        logger.error("Update code source error, SQL:{}".format(sql))
        disconnect_database(conn=conn, cursor=cursor, logger=logger)
        return False
    conn.commit()

    disconnect_database(conn=conn, cursor=cursor, logger=logger)
    return True


def get_project_id_by_name(project_name:str, logger:logging.Logger, mdb_file_name:str="caseManage.mdb")->str:
    table_name = "ProjectInformation"
    base_key = "ProjectName"
    target_key = "ID"
    return get_item_value(table_name=table_name, target_key=target_key, base_key=base_key, base_value=project_name, logger=logger)


def update_item_by_project_id(project_id:str, item_key:str, item_value:str, logger:logging.Logger, mdb_file_name:str="caseManage.mdb")->bool:
    table_name = "ProjectInformation"
    base_key = 'ID'
    project_id = int(project_id)
    return update_item_value(table_name=table_name, base_key=base_key, base_value=project_id,
                             target_key=item_key, target_value=item_value, logger=logger)


def update_item_by_project_name(project_name:str, item_key:str, item_value:str, logger:logging.Logger)->bool:
    project_id = get_project_id_by_name(project_name=project_name, logger=logger)
    project_id = int(project_id)
    return update_item_by_project_id(project_id=project_id, item_key=item_key, item_value=item_value, logger=logger)


def update_code_source(project_id:int, code_source:str, logger:logging.Logger)->bool:
    return update_item_by_project_id(project_id=project_id, item_key="SourcePath", item_value=code_source, logger=logger)


def update_compile_config_by_project_name(project_name:str, compile_cfg:str, logger:logging.Logger):
    project_id = get_project_id_by_name(project_name=project_name, logger=logger)
    project_id = int(project_id)
    return update_item_by_project_id(project_id=project_id, item_key="CompileCfg", item_value=compile_cfg, logger=logger)


def update_test_type_by_prject_name(project_name:str, test_type:str, logger:logging.Logger):
    project_id = get_project_id_by_name(project_name=project_name, logger=logger)
    project_id = int(project_id)
    return update_item_by_project_id(project_id=project_id, item_key="TestType", item_value=test_type, logger=logger)


def get_test_type(project_id:str, logger:logging.Logger, mdb_file_name:str="caseManage.mdb"):
    table_name = "ProjectInformation"
    base_key = "ID"
    target_key = "TestType"
    return get_item_value(table_name=table_name, target_key=target_key, base_key=base_key, base_value=project_id, logger=logger)

def get_compile_cfg(project_id:str, logger:logging.Logger, mdb_file_name:str="caseManage.mdb"):
    table_name = "ProjectInformation"
    base_key = "ID"
    target_key = "CompileCfg"
    project_id = int(project_id)
    return get_item_value(table_name=table_name, target_key=target_key, base_key=base_key, base_value=project_id, logger=logger)


def set_code_source(project_id:int, code_source:str, logger:logging.Logger,
                     mdb_file_name:str="caseManage.mdb")->str:
    return update_item_by_project_id(project_id=project_id, item_key="SourcePath", item_value=code_source, logger=logger)


def get_code_source(project_id:int, logger:logging.Logger, mdb_file_name:str="caseManage.mdb")->str:
    table_name = "ProjectInformation"
    base_key = "ID"
    target_key = "SourcePath"
    return get_item_value(table_name=table_name, target_key=target_key, base_key=base_key, base_value=project_id, logger=logger)


def get_project_name(project_id:int, logger:logging.Logger, mdb_file_name="caseManage.mdb")->str:
    table_name = "ProjectInformation"
    base_key = "ID"
    target_key = "ProjectName"
    return get_item_value(table_name=table_name, target_key=target_key, base_key=base_key, base_value=project_id, logger=logger)


def set_project_path(project_id:int, project_path:str, logger:logging.Logger,
                     mdb_file_name:str="caseManage.mdb")->str:
    return update_item_by_project_id(project_id=project_id, item_key="ProjectPath", item_value=project_path, logger=logger)


def get_project_path(project_id:int, logger:logging.Logger, mdb_file_name:str="caseManage.mdb")->str:
    table_name = "ProjectInformation"
    base_key = "ID"
    target_key = "ProjectPath"
    project_id = int(project_id)
    return get_item_value(table_name=table_name, target_key=target_key, base_key=base_key, base_value=project_id, logger=logger)


def set_ide_path(project_id:int, ide_path:str, logger:logging.Logger,
                 mdb_file_name:str="caseManage.mdb")->str:
    return update_item_by_project_id(project_id=project_id, item_key="idePath", item_value=ide_path, logger=logger)


def get_ide_path(project_id:str, logger: logging.Logger, mdb_file_name:str="caseManage.mdb")->str:
    table_name = "ProjectInformation"
    base_key = "ID"
    target_key = "idePath"
    project_id = int(project_id)
    return get_item_value(table_name=table_name, target_key=target_key, base_key=base_key, base_value=project_id, logger=logger)


def get_node_name(project_id:int, module_id:str, sub_id:str, logger:logging.Logger, mdb_file_name:str="caseManage.mdb")->str:
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
        disconnect_database(conn=conn, cursor=cursor, logger=logger)
        return None
    rows = cursor.fetchall()
    if len(rows) != 1:
        logger.error("Get node name error, get item: {}".format(len(rows)))
        disconnect_database(conn=conn, cursor=cursor, logger=logger)
        return None

    node_name = rows[0][0]
    disconnect_database(conn=conn, cursor=cursor, logger=logger)
    return node_name


def debug_show_table_info(logger):
    table_name = "ProjectInformation"
    # table_name = "TestCase"
    show_table_info_table(table_name=table_name)
    show_table_column(table_name=table_name, logger=logger)
    return


def debug_add_compile_cfg_for_project_info(logger):
    table_name = "ProjectInformation"
    debug_show_table_info(logger)
    add_new_colum(table_name=table_name, colum_name="CompileCfg", colum_type="varchar(32)", logger=logger)
    show_table_column(table_name=table_name, logger=logger)
    update_compile_config_by_project_name(project_name="EAM2011", compile_cfg="Debug", logger=logger)
    update_compile_config_by_project_name(project_name="E3640", compile_cfg="FlashDebug", logger=logger)
    debug_show_table_info(logger)
    return


def debug_add_test_type_for_project_info(logger):
    table_name = "ProjectInformation"
    debug_show_table_info(logger)
    update_test_type_by_prject_name(project_name="EAM2011", test_type="CanTrigger", logger=logger)
    update_test_type_by_prject_name(project_name="E3640", test_type="AutoProc", logger=logger)
    debug_show_table_info(logger)
    return


def debug_check_compile_cfg(logger):
    compile_cfg = get_compile_cfg(project_id="1", logger=logger)
    print("EAM2011 compile config: *{}*".format(compile_cfg))
    compile_cfg = get_compile_cfg(project_id="2", logger=logger)
    print("E360 compile config: *{}*".format(compile_cfg))


def debug_get_test_node_name(logger):
    # Project - E3640
    project_id="2"
    module_id = "MODULE_ID_SM4"
    sub_id = "0x0001"
    test_node_name = get_node_name(project_id=project_id, module_id=module_id, sub_id=sub_id, logger=logger)
    print("Module_id = {}, sub_id = {}, test_node = \"{}\"".format(module_id, sub_id, test_node_name))
    module_id = "MODULE_ID_RSA"
    sub_id = "0x0001"
    test_node_name = get_node_name(project_id=project_id, module_id=module_id, sub_id=sub_id, logger=logger)
    print("Module_id = {}, sub_id = {}, test_node = \"{}\"".format(module_id, sub_id, test_node_name))

if __name__ == "__main__":
    clean_log_files()
    logger = get_logger("DBA_Log")
    debug_show_table_info(logger)
    conn_list = []
    for i in range(10000):
        try:
            conn, cursor = connect_database(logger, "caseManage.mdb")
        except:
            logger.error("Connect error, break process, time = {}".format(i))
            break
        conn_list.append({"conn":conn, "cursor":cursor})

        table_name = "ProjectInformation"
        base_key = "ID"
        target_key = "ProjectName"
        sql = "SELECT {target_key} FROM {table_name} WHERE {base_key}={base_value}".format(
            table_name=table_name, target_key=target_key, base_key=base_key, base_value=2
        )
        logger.info("SQL: {}".format(sql))
        try:
            conn_list[i]["cursor"].execute(sql)
        except:
            logger.error("Execute SQL error, time={}".format(i))
            continue

        rows = conn_list[i]["cursor"].fetchall()
        if len(rows) != 1:
            logger.error("Get code source error, time: {}".format(i))
            continue

        target_value = rows[0][0]
        logger.info("ProjectName: {}".format(target_value))
        conn_list[i]["cursor"].close()
        conn_list[i]["conn"].close()
        print("{} connect".format(i))
