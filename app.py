# -*- coding: utf-8 -*-
"""
完整的6表协作系统 - NiceGUI 应用
法律+人力部门协作的财务合规系统
"""

from openpyxl.utils import get_column_letter
from nicegui import ui, app
import sqlite3
import pandas as pd
import os
import webbrowser
import threading
import sys
from nicegui import app

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from calculation_engine import CalculationEngine
from column_maps import COLUMN_MAP
from import_service import (
    upload_hr_payroll_bytes,
    upload_hr_roster_bytes,
upload_hr_risk_fund_bytes,
upload_hr_risk_fund_extended_bytes,
upload_legal_accountability_bytes,
upload_legal_economic_detail_v2_bytes,
upload_legal_economic_detail_bytes
)

DB_NAME = 'data.db'


def get_conn():
    return sqlite3.connect(DB_NAME)


# ==================== 初始化数据库 ====================

def init_database():
    """初始化数据库，创建所有表"""
    conn = get_conn()
    cursor = conn.cursor()

    # 读取 SQL 脚本
    sql_script = """
    -- 1. 人力工资表
    CREATE TABLE IF NOT EXISTS hr_payroll (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sequence_no TEXT,
        date TEXT NOT NULL,
        id_number TEXT,
        employee_id TEXT NOT NULL,
        employee_name TEXT,
        organization TEXT,
        department TEXT,
        front_middle_back TEXT,
        position_title TEXT,
        entry_date TEXT,
        remark TEXT,
        organization_level TEXT,
        organization_type TEXT,
        salary_category TEXT,
        salary_grade TEXT,
        salary_level TEXT,
        position_salary REAL,
        dept_monthly_perf REAL,
        line_perf REAL,
        dept_quarterly_perf REAL,
        line_special_award REAL,
        settlement_perf REAL,
        hard_target REAL,
        performance_adjustment REAL,
        total_perf REAL,
        tax_pre_accountability_perf REAL,
        deferred_ratio REAL,
        deferred_salary REAL,
        post_deferred_perf REAL,
        position_adjustment REAL,
        allowance REAL,
        study_award REAL,
        overtime REAL,
        award_punishment REAL,
        temp_allowance REAL,
        release_deferred REAL,
        previous_year_release REAL,
        attendance_deduct REAL,
        taxable_total REAL,
        personal_pension REAL,
        personal_medical REAL,
        personal_unemployment REAL,
        personal_pension_fund REAL,
        personal_pension_supp REAL,
        personal_medical_supp REAL,
        personal_unemployment_supp REAL,
        personal_pension_fund_supp REAL,
        personal_annuity REAL,
        income_tax REAL,
        tax_supp REAL,
        accountability REAL,
        union_fee REAL,
        actual_payment REAL,
        personnel_category TEXT,
        doc_number TEXT ,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(date, employee_id,doc_number)
    );

    CREATE INDEX IF NOT EXISTS idx_hr_payroll_date_emp ON hr_payroll(date, employee_id,doc_number);
    CREATE INDEX IF NOT EXISTS idx_hr_payroll_emp_year ON hr_payroll(employee_id, substr(date, 1, 4));

    -- 2. 人力花名册
    CREATE TABLE IF NOT EXISTS hr_roster (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sequence_no TEXT,
        employee_id TEXT NOT NULL UNIQUE,
        employee_name TEXT,
        organization TEXT,
        department TEXT,
        main_position TEXT,
        position_title TEXT,
        political_status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_hr_roster_emp ON hr_roster(employee_id);

    -- 3. 人力风险金
    CREATE TABLE IF NOT EXISTS hr_risk_fund (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sequence_no TEXT,
        employee_id TEXT NOT NULL,
        employee_name TEXT,
        organization TEXT,
        working_status TEXT,
        year INTEGER NOT NULL,
        month_01 REAL DEFAULT 0,
        month_02 REAL DEFAULT 0,
        month_03 REAL DEFAULT 0,
        month_04 REAL DEFAULT 0,
        month_05 REAL DEFAULT 0,
        month_06 REAL DEFAULT 0,
        month_07 REAL DEFAULT 0,
        month_08 REAL DEFAULT 0,
        month_09 REAL DEFAULT 0,
        month_10 REAL DEFAULT 0,
        month_11 REAL DEFAULT 0,
        month_12 REAL DEFAULT 0,
        annual_deferred REAL,
        cumulative_deferred REAL,
        calc_flag INTEGER DEFAULT 0,   
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(employee_id, year)
    );

    CREATE INDEX IF NOT EXISTS idx_hr_risk_fund_emp_year ON hr_risk_fund(employee_id, year);

    -- 4. 人力风险金延伸
    CREATE TABLE IF NOT EXISTS hr_risk_fund_extended (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sequence_no TEXT,
        date TEXT NOT NULL,
        employee_id TEXT NOT NULL,
        employee_name TEXT,
        organization TEXT,
        working_status TEXT,
        n4_committee_defer REAL DEFAULT 0,
        n4_credit_deduct REAL DEFAULT 0,
        n4_bifurcated_defer REAL DEFAULT 0,
        n4_other REAL DEFAULT 0,
        n3_committee_defer REAL DEFAULT 0,
        n3_credit_deduct REAL DEFAULT 0,
        n3_bifurcated_defer REAL DEFAULT 0,
        n3_other REAL DEFAULT 0,
        n2_committee_defer REAL DEFAULT 0,
        n2_credit_deduct REAL DEFAULT 0,
        n2_bifurcated_defer REAL DEFAULT 0,
        n2_other REAL DEFAULT 0,
        exec_date TEXT,
        remark TEXT,
        n4_balance REAL,
        n3_balance REAL,
        n2_balance REAL,
        balance_total REAL,
        n4_repay_pending REAL,
        n4_accountability_deduct REAL,
        n4_actual_repay REAL,
        n3_repay_pending REAL,
        n3_accountability_deduct REAL,
        n3_actual_repay REAL,
        n2_repay_pending REAL,
        n2_accountability_deduct REAL,
        n2_actual_repay REAL,
        annual_repay_total REAL,
        accountability_actual_tax_pre REAL,
        accountability_actual_tax_post REAL,
        accountability_provide_tax_pre REAL,
        accountability_provide_tax_post REAL,
        doc_number TEXT,
        n4_after_exec_balance REAL,
        n3_after_exec_balance REAL,
        n2_after_exec_balance REAL,
        final_balance REAL,
        calc_flag INTEGER DEFAULT 0,   
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(date, employee_id)
    );

    CREATE INDEX IF NOT EXISTS idx_hr_risk_ext_date_emp ON hr_risk_fund_extended(date, employee_id);

    -- 5. 法律经济处理明细表
    CREATE TABLE IF NOT EXISTS legal_economic_detail (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sequence_no TEXT,
        date TEXT NOT NULL,
        employee_id TEXT NOT NULL,
        doc_number TEXT NOT NULL,
        employee_name TEXT,
        organization TEXT,
        file_name TEXT,
        issue_date TEXT,
        tax_pre REAL,
        tax_post REAL,
        discipline TEXT,
        salary_year INTEGER,
        coefficient REAL,
        remark TEXT,
        accounting_amount REAL,
        status TEXT DEFAULT '待下载',
        calc_flag INTEGER DEFAULT 0,   
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE( date, employee_id, doc_number)
    );

    CREATE INDEX IF NOT EXISTS idx_legal_econ_date_emp_doc ON legal_economic_detail(date, employee_id, doc_number);

    -- 6. 法律问责办台账

    CREATE TABLE IF NOT EXISTS legal_accountability (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sequence_no TEXT,
        branch TEXT,
        employee_id TEXT NOT NULL,
        employee_name TEXT,
        original_organization TEXT,
        original_position_category TEXT,
        original_position_title TEXT,
        current_organization TEXT,
        current_position_category TEXT,
        current_position_title TEXT,
        employee_status TEXT,
        violation_source TEXT,
        violation_attribution TEXT,
        violation_description TEXT,
        violation_discovery_date TEXT,
        accountability_project TEXT,
        doc_number TEXT NOT NULL,
        accountability_authority TEXT,
        decision_body TEXT,
        issue_date TEXT,
        handling_basis TEXT,
        discipline_type TEXT,
        tax_pre REAL,
        tax_post REAL,
        total_economic REAL,
        main_pay_tax_pre REAL,
        main_pay_tax_post REAL,
        exec_date_legal TEXT,
        exec_date_hr TEXT,
        criticism TEXT,
        remark TEXT,
        conference TEXT,
        political_status TEXT,
        performance_adjustment REAL,
        accountability_tax_post REAL,
        risk_deduction REAL,
        tax_pre_exec REAL,
        tax_pre_pending REAL,
        tax_post_exec REAL,
        tax_post_pending REAL,
        exec_total REAL,
        unexec_total REAL,
        cumulative_performance REAL,
        cumulative_risk REAL,
        calc_flag INTEGER DEFAULT 0,   
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(employee_id, doc_number, exec_date_hr)
    );
    CREATE INDEX IF NOT EXISTS idx_legal_emp_doc ON legal_accountability(employee_id, doc_number);
    CREATE INDEX IF NOT EXISTS idx_legal_acct_emp_date ON legal_accountability(employee_id, doc_number, exec_date_hr);
    
    ---新增用户信息表
    CREATE TABLE IF NOT EXISTS sys_user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
    );
    
    """

    for statement in sql_script.split(';'):
        if statement.strip():
            cursor.execute(statement)

    cursor.execute("INSERT OR IGNORE INTO sys_user (username,password,role) VALUES ('admin','123456','admin')")
    cursor.execute("INSERT OR IGNORE INTO sys_user (username,password,role) VALUES ('legal','123456','legal')")

    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")



init_database()
engine = CalculationEngine(DB_NAME)


# ==================== UI 页面 ====================
@ui.page('/login')
def login_page():

    # 背景
    with ui.element('div').classes('w-full h-screen flex items-center justify-center') \
            .style('background: linear-gradient(135deg, #667eea, #764ba2);'):

        # 登录卡片
        with ui.card().classes('w-[360px] p-6 shadow-2xl rounded-2xl'):

            ui.label('🔐 系统登录') \
                .classes('text-2xl font-bold text-center mb-4') \
                .style('color:#333')

            username = ui.input(
                label='用户名',
                placeholder='请输入用户名'
            ).classes('w-full')

            password = ui.input(
                label='密码',
                placeholder='请输入密码',
                password=True
            ).classes('w-full')

            msg = ui.label('').classes('text-center text-sm')

            def do_login():
                msg.set_text('')
                msg.style('color: gray')

                conn = get_conn()
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT username, role FROM sys_user
                    WHERE username=? AND password=?
                """, (username.value, password.value))

                user = cursor.fetchone()
                conn.close()

                if user:
                    app.storage.user['username'] = user[0]
                    app.storage.user['role'] = user[1]
                    ui.navigate.to('/')
                else:
                    msg.set_text('❌ 用户名或密码错误')
                    msg.style('color:red')

            ui.button(
                '登录',
                on_click=do_login
            ).classes('w-full mt-4 bg-blue-500 text-white text-lg')

            ui.separator()

            ui.label('请输入账号密码登录') \
                .classes('text-xs text-gray-500 text-center')

@ui.page('/')
def main_page():
    # ✅ 登录校验
    if 'username' not in app.storage.user:
        ui.navigate.to('/login')
        return

    role = app.storage.user.get('role')
    ui.label('📋 6表协作系统 - 法律+人力部门财务合规').classes('text-h3').style('color: #2196F3')

    def open_change_pwd_dialog():
        dialog = ui.dialog()
        with dialog, ui.card():
            ui.label('修改密码').classes('text-h6')

            old_pwd = ui.input('原密码', password=True)
            new_pwd = ui.input('新密码', password=True)
            new_pwd2 = ui.input('确认新密码', password=True)

            msg = ui.label('')

            def submit():
                username = app.storage.user.get('username')

                if new_pwd.value != new_pwd2.value:
                    msg.set_text('❌ 两次密码不一致')
                    msg.style('color:red')
                    return

                conn = get_conn()
                cursor = conn.cursor()

                # 校验旧密码
                cursor.execute("""
                    SELECT 1 FROM sys_user
                    WHERE username=? AND password=?
                """, (username, old_pwd.value))

                if not cursor.fetchone():
                    msg.set_text('❌ 原密码错误')
                    msg.style('color:red')
                    conn.close()
                    return

                # 更新密码
                cursor.execute("""
                    UPDATE sys_user
                    SET password=?
                    WHERE username=?
                """, (new_pwd.value, username))

                conn.commit()
                conn.close()

                msg.set_text('✅ 修改成功')
                msg.style('color:green')

            with ui.row():
                ui.button('提交', on_click=submit).classes('bg-green-500 text-white')
                ui.button('关闭', on_click=dialog.close)

        dialog.open()

    with ui.row().classes('justify-between w-full'):
        ui.label(f"当前用户：{app.storage.user['username']}（{role}）")

        with ui.row():
            ui.button('修改密码', on_click=lambda: open_change_pwd_dialog()) \
                .classes('bg-blue-500 text-white')

            def logout():
                app.storage.user.clear()
                ui.navigate.to('/login')

            ui.button('退出登录', on_click=logout).classes('bg-red-500 text-white')
    ui.separator()

    with ui.tabs() as tabs:

        if role == 'admin':
            ui.tab('tab1', label='1️⃣ 基础导入')
            ui.tab('tab2', label='2️⃣ 自动计算')
            ui.tab('tab3', label='3️⃣ 法律部二次处理')
            ui.tab('tab4', label='4️⃣ 其他数据导入')
            ui.tab('tab5', label='5️⃣ 数据导出')
            ui.tab('tab6', label='❓ 帮助')
        else:
            # 👤 legal
            ui.tab('tab2', label='2️⃣ 自动计算')
            ui.tab('tab3', label='3️⃣ 法律部二次处理')
            ui.tab('tab4', label='4️⃣ 其他数据导入')
            ui.tab('tab6', label='❓ 帮助')

    default_tab = 'tab1' if role == 'admin' else 'tab2'

    panels = ui.tab_panels(tabs, value=default_tab).classes('w-full')


    with panels:

        # ========== Tab 1: 基础导入 ==========
        with ui.tab_panel('tab1'):
            ui.label('人力部导入基础数据').classes('text-h6')

            with ui.row().classes('gap-4'):

                # ================= 工资表 =================
                with ui.column().classes('w-1/2'):
                    ui.label('📊 人力工资表').classes('text-base font-bold')

                    payroll_status = ui.label('')

                    async def handle_payroll_upload(e):
                        payroll_status.set_text('📥 上传中...')
                        payroll_status.style('color: gray')

                        try:
                            # ✅ 统一读取（兼容所有版本）
                            file_obj = getattr(e, 'file', e)

                            # 文件名
                            filename = getattr(file_obj, 'filename', None) \
                                       or getattr(file_obj, 'name', None) \
                                       or 'unknown.xlsx'

                            # 文件内容（关键：统一 bytes）
                            if hasattr(file_obj, 'read'):
                                content = await file_obj.read()
                            else:
                                content = file_obj.content.read()

                            # ✅ 直接调用你新的核心函数（bytes版）
                            result = upload_hr_payroll_bytes(content, filename)

                            if result.get('success'):
                                payroll_status.set_text('✅ ' + result.get('message', '成功'))
                                payroll_status.style('color: green')
                            else:
                                payroll_status.set_text('❌ ' + result.get('message', '失败'))
                                payroll_status.style('color: red')

                        except Exception as ex:
                            payroll_status.set_text(f'❌ 上传失败: {str(ex)}')
                            payroll_status.style('color: red')

                    ui.upload(
                        label='选择工资表（自动上传）',
                        on_upload=handle_payroll_upload,
                        auto_upload=True
                    ).classes('w-full')

                # ================= 花名册 =================
                with ui.column().classes('w-1/2'):
                    ui.label('👥 人力花名册').classes('text-base font-bold')

                    roster_status = ui.label('')

                    async def handle_roster_upload(e):
                        roster_status.set_text('📥 上传中...')
                        roster_status.style('color: gray')

                        try:
                            file_obj = getattr(e, 'file', e)

                            filename = getattr(file_obj, 'filename', None) \
                                       or getattr(file_obj, 'name', None) \
                                       or 'unknown.xlsx'

                            if hasattr(file_obj, 'read'):
                                content = await file_obj.read()
                            else:
                                content = file_obj.content.read()

                            result = upload_hr_roster_bytes(content, filename)

                            if result.get('success'):
                                roster_status.set_text('✅ ' + result.get('message', '成功'))
                                roster_status.style('color: green')
                            else:
                                roster_status.set_text('❌ ' + result.get('message', '失败'))
                                roster_status.style('color: red')

                        except Exception as ex:
                            roster_status.set_text(f'❌ 上传失败: {str(ex)}')
                            roster_status.style('color: red')

                    ui.upload(
                        label='选择花名册（自动上传）',
                        on_upload=handle_roster_upload,
                        auto_upload=True
                    ).classes('w-full')

        # ========== Tab 2: 自动计算结果 ==========
        with ui.tab_panel('tab2'):

            ui.label('系统自动计算的表').classes('text-h6')

            # =============================
            # 通用函数
            # =============================

            def load_data(sql):
                conn = get_conn()
                df = pd.read_sql(sql, conn)
                conn.close()
                return df

            def format_dataframe(df, table_name):
                df = df.drop(columns=['id'], errors='ignore')
                if table_name in COLUMN_MAP:
                    df = df.rename(columns=COLUMN_MAP[table_name])
                return df

            def write_excel(writer, df, sheet_name):
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                worksheet = writer.sheets[sheet_name]
                worksheet.freeze_panes = 'A2'
                worksheet.auto_filter.ref = worksheet.dimensions

                for i, column in enumerate(df.columns, 1):
                    col_letter = get_column_letter(i)
                    worksheet.column_dimensions[col_letter].width = 18

            def download_excel(sql, table_name, filename):
                df = load_data(sql)
                df = format_dataframe(df, table_name)
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    write_excel(writer, df, 'sheet1')
                ui.download(filename)


            # =============================
            # 表配置（按权限控制）
            # =============================

            if role == 'admin':
                TAB_CONFIG = [
                    {
                        "name": "人力风险金",
                        "table": "hr_risk_fund",
                        "preview_sql": "SELECT * FROM hr_risk_fund ORDER BY employee_id, year DESC LIMIT 20",
                        "download_sql": "SELECT * FROM hr_risk_fund ORDER BY employee_id, year",
                        "file": "人力风险金.xlsx",
                        "empty": "暂无数据 - 请先导入工资表"
                    },
                    {
                        "name": "人力风险金延伸",
                        "table": "hr_risk_fund_extended",
                        "preview_sql": "SELECT * FROM hr_risk_fund_extended ORDER BY employee_id, date DESC LIMIT 20",
                        "download_sql": "SELECT * FROM hr_risk_fund_extended ORDER BY employee_id, date",
                        "file": "人力风险金延伸.xlsx",
                        "empty": "暂无数据 - 请先导入数据"
                    },
                    {
                        "name": "法律经济处理明细",
                        "table": "legal_economic_detail",
                        "preview_sql": "SELECT * FROM legal_economic_detail ORDER BY date DESC LIMIT 20",
                        "download_sql": "SELECT * FROM legal_economic_detail ORDER BY date",
                        "file": "法律经济处理明细表.xlsx",
                        "empty": "暂无数据 - 请先生成"
                    },
                    {
                        "name": "法律问责办台账",
                        "table": "legal_accountability",
                        "preview_sql": "SELECT * FROM legal_accountability ORDER BY employee_id, exec_date_hr DESC LIMIT 20",
                        "download_sql": "SELECT * FROM legal_accountability ORDER BY employee_id, exec_date_hr",
                        "file": "法律问责办台账.xlsx",
                        "empty": "暂无数据"
                    },
                    {
                        "name": "人力工资表",
                        "table": "hr_payroll",
                        "preview_sql": "SELECT * FROM hr_payroll ORDER BY employee_id, date DESC LIMIT 20",
                        "download_sql": "SELECT * FROM hr_payroll ORDER BY employee_id, date",
                        "file": "人力工资表.xlsx",
                        "empty": "暂无数据"
                    },
                    {
                        "name": "人力花名册",
                        "table": "hr_roster",
                        "preview_sql": "SELECT * FROM hr_roster ORDER BY employee_id DESC LIMIT 20",
                        "download_sql": "SELECT * FROM hr_roster ORDER BY employee_id",
                        "file": "人力花名册.xlsx",
                        "empty": "暂无数据"
                    }
                ]
            else:
            # 👤 legal 只看2张表
                TAB_CONFIG = [
                    {
                        "name": "法律经济处理明细",
                        "table": "legal_economic_detail",
                        "preview_sql": "SELECT * FROM legal_economic_detail ORDER BY date DESC LIMIT 20",
                        "download_sql": "SELECT * FROM legal_economic_detail ORDER BY date",
                        "file": "法律经济处理明细表.xlsx",
                        "empty": "暂无数据 - 请先生成"
                    },
                    {
                        "name": "法律问责办台账",
                        "table": "legal_accountability",
                        "preview_sql": "SELECT * FROM legal_accountability ORDER BY employee_id, exec_date_hr DESC LIMIT 20",
                        "download_sql": "SELECT * FROM legal_accountability ORDER BY employee_id, exec_date_hr",
                        "file": "法律问责办台账.xlsx",
                        "empty": "暂无数据"
                    }
                ]


            # =============================
            # 核心：动态刷新组件
            # =============================

            TABLE_CACHE = {}

            def refresh_table(table, conf):
                df = load_data(conf["preview_sql"])

                if not df.empty:
                    df = format_dataframe(df, conf["table"])

                    # ⭐ 关键：设置列
                    table.columns = [
                        {"name": col, "label": col, "field": col}
                        for col in df.columns
                    ]

                    table.rows = df.head(10).to_dict('records')
                else:
                    table.rows = []
                    table.columns = []

                table.update()

            # =============================
            # Tabs
            # =============================

            with ui.tabs() as subtabs:
                tabs = [ui.tab(c["name"]) for c in TAB_CONFIG]

            with ui.tab_panels(subtabs, value=tabs[0]).classes('w-full'):

                for tab, conf in zip(tabs, TAB_CONFIG):
                    with ui.tab_panel(tab):
                        # 空表先创建（关键！）
                        table = ui.table(
                            columns=[],
                            rows=[]
                        ).props('dense separator=cell').classes('w-full')

                        TABLE_CACHE[conf["table"]] = (table, conf)

                        # 按钮区
                        with ui.row():
                            ui.button(
                                f'📥 下载{conf["name"]}',
                                on_click=lambda c=conf: download_excel(
                                    c["download_sql"],
                                    c["table"],
                                    c["file"]
                                )
                            ).classes('bg-blue-500 text-white')

                            ui.button(
                                '🔄 刷新数据',
                                on_click=lambda t=table, c=conf: refresh_table(t, c)
                            ).classes('bg-green-500 text-white')

                        # ⭐ 关键：Tab激活时加载数据
                        tab.on('click', lambda t=table, c=conf: refresh_table(t, c))

            # =============================
            # ⭐ 可选：自动刷新（全局）
            # =============================

            def refresh_all():
                for table, conf in TABLE_CACHE.values():
                    refresh_table(table, conf)

            # 每10秒自动刷新（可调）
            ui.timer(10, refresh_all)

        # ========== Tab 3: 法律部二次处理 ==========
        with ui.tab_panel('tab3'):
            ui.label('⚠️ 法律部工作流程').classes('text-h6').style('color: #FF6B6B')

            ui.markdown('''
            操作步骤：

            1. 📥 下载 经济处理明细表(v1) - 包含自动计算的 核算金额
            2. ✏️ 修改 表中的 税前 和 税后 两列
            3. 📤 重新上传 经济处理明细表(v2)
            4. ✅ 系统自动更新关联表
            ''')

            with ui.row().classes('gap-4'):

                # ================= 下载 =================
                def download_for_legal():
                    conn = get_conn()
                    df = pd.read_sql("""
                        SELECT * FROM legal_economic_detail WHERE status = '待下载'
                    """, conn)
                    conn.close()

                    if df.empty:
                        ui.notify('暂无数据', color='warning')
                        return

                    df = df.drop(columns=['id'], errors='ignore')
                    df.rename(columns=COLUMN_MAP["legal_economic_detail"], inplace=True)

                    file_name = '法律经济处理明细表_v1.xlsx'
                    df.to_excel(file_name, index=False)
                    ui.download(file_name)

                ui.button('📥 下载 v1 版本（修改用）', on_click=download_for_legal) \
                    .classes('bg-[#FF6B6B] text-white')

                # ================= 上传 v2 =================
                with ui.column().classes('w-1/2'):
                    ui.label('📤 上传 v2（修改后）').classes('text-base font-bold')

                    status_container = ui.column()  # ⭐关键

                    def update_status(text, color):
                        status_container.clear()
                        with status_container:
                            ui.label(text).classes(f'text-base font-bold text-{color}')

                    update_status('等待上传...', 'gray')

                    async def handle_legal_upload(e):
                        update_status('📥 上传中...', 'gray')

                        try:
                            file_obj = getattr(e, 'file', e)

                            filename = getattr(file_obj, 'filename', None) \
                                       or getattr(file_obj, 'name', None) \
                                       or 'unknown.xlsx'

                            if hasattr(file_obj, 'read'):
                                content = await file_obj.read()
                            else:
                                content = file_obj.content.read()

                            result = upload_legal_economic_detail_v2_bytes(content, filename)

                            msg = result.get('message', '')

                            if result.get('success'):
                                update_status('✅ ' + msg, 'green')
                                ui.notify(msg, type='positive')
                            else:
                                update_status('❌ ' + msg, 'red')
                                ui.notify(msg, type='negative')

                        except Exception as ex:
                            update_status(f'❌ 上传失败: {str(ex)}', 'red')

                    ui.upload(
                        label='选择已修改的文件（自动上传）',
                        on_upload=handle_legal_upload,
                        auto_upload=True
                    ).classes('w-full')

        # ========== Tab 4: 其他导入 ==========
        with ui.tab_panel('tab4'):
            ui.label('风险金延伸 & 问责办台账导入').classes('text-h6')

            with ui.row().classes('w-full gap-6 items-start').style('flex-wrap:nowrap'):

                # ======================
                # 左侧：上传区（已改成 Tab1 模式）
                # ======================
                with ui.column().classes('flex-1'):

                    with ui.row().classes('gap-4'):

                        # ================= 法律经济处理明细 =================
                        with ui.column().classes('w-1/2'):
                            ui.label('📑 法律经济处理明细表').classes('text-base font-bold')

                            legal_status = ui.label('')

                            async def handle_legal_upload(e):
                                legal_status.set_text('📥 上传中...')
                                legal_status.style('color: gray')

                                try:
                                    file_obj = getattr(e, 'file', e)

                                    filename = getattr(file_obj, 'filename', None) \
                                               or getattr(file_obj, 'name', None) \
                                               or 'unknown.xlsx'

                                    if hasattr(file_obj, 'read'):
                                        content = await file_obj.read()
                                    else:
                                        content = file_obj.content.read()

                                    result = upload_legal_economic_detail_bytes(content, filename)

                                    if result.get('success'):
                                        legal_status.set_text('✅ ' + result.get('message', '成功'))
                                        legal_status.style('color: green')
                                    else:
                                        legal_status.set_text('❌ ' + result.get('message', '失败'))
                                        legal_status.style('color: red')

                                except Exception as ex:
                                    legal_status.set_text(f'❌ 上传失败: {str(ex)}')
                                    legal_status.style('color: red')

                            ui.upload(
                                label='选择法律明细（自动上传）',
                                on_upload=handle_legal_upload,
                                auto_upload=True
                            ).classes('w-full')

                        # ================= 问责办台账 =================
                        with ui.column().classes('w-1/2'):
                            ui.label('📊 法律问责办台账').classes('text-base font-bold')

                            acct_status = ui.label('')

                            async def handle_acct_upload(e):
                                acct_status.set_text('📥 上传中...')
                                acct_status.style('color: gray')

                                try:
                                    file_obj = getattr(e, 'file', e)

                                    filename = getattr(file_obj, 'filename', None) \
                                               or getattr(file_obj, 'name', None) \
                                               or 'unknown.xlsx'

                                    if hasattr(file_obj, 'read'):
                                        content = await file_obj.read()
                                    else:
                                        content = file_obj.content.read()

                                    result = upload_legal_accountability_bytes(content, filename)

                                    if result.get('success'):
                                        acct_status.set_text('✅ ' + result.get('message', '成功'))
                                        acct_status.style('color: green')
                                    else:
                                        acct_status.set_text('❌ ' + result.get('message', '失败'))
                                        acct_status.style('color: red')

                                except Exception as ex:
                                    acct_status.set_text(f'❌ 上传失败: {str(ex)}')
                                    acct_status.style('color: red')

                            ui.upload(
                                label='选择问责台账（自动上传）',
                                on_upload=handle_acct_upload,
                                auto_upload=True
                            ).classes('w-full')

                    with ui.row().classes('gap-4 mt-4'):

                        # ================= 人力风险金 =================
                        with ui.column().classes('w-1/2'):
                            ui.label('💰 人力风险金').classes('text-base font-bold')

                            risk_status = ui.label('')

                            async def handle_risk_upload(e):
                                risk_status.set_text('📥 上传中...')
                                risk_status.style('color: gray')

                                try:
                                    file_obj = getattr(e, 'file', e)

                                    filename = getattr(file_obj, 'filename', None) \
                                               or getattr(file_obj, 'name', None) \
                                               or 'unknown.xlsx'

                                    if hasattr(file_obj, 'read'):
                                        content = await file_obj.read()
                                    else:
                                        content = file_obj.content.read()

                                    result = upload_hr_risk_fund_bytes(content, filename)

                                    if result.get('success'):
                                        risk_status.set_text('✅ ' + result.get('message', '成功'))
                                        risk_status.style('color: green')
                                    else:
                                        risk_status.set_text('❌ ' + result.get('message', '失败'))
                                        risk_status.style('color: red')

                                except Exception as ex:
                                    risk_status.set_text(f'❌ 上传失败: {str(ex)}')
                                    risk_status.style('color: red')

                            ui.upload(
                                label='选择风险金（自动上传）',
                                on_upload=handle_risk_upload,
                                auto_upload=True
                            ).classes('w-full')

                        # ================= 风险金延伸 =================
                        with ui.column().classes('w-1/2'):
                            ui.label('⚙️ 人力风险金延伸').classes('text-base font-bold')

                            risk_ext_status = ui.label('')

                            async def handle_risk_ext_upload(e):
                                risk_ext_status.set_text('📥 上传中...')
                                risk_ext_status.style('color: gray')

                                try:
                                    file_obj = getattr(e, 'file', e)

                                    filename = getattr(file_obj, 'filename', None) \
                                               or getattr(file_obj, 'name', None) \
                                               or 'unknown.xlsx'

                                    if hasattr(file_obj, 'read'):
                                        content = await file_obj.read()
                                    else:
                                        content = file_obj.content.read()

                                    result = upload_hr_risk_fund_extended_bytes(content, filename)

                                    if result.get('success'):
                                        risk_ext_status.set_text('✅ ' + result.get('message', '成功'))
                                        risk_ext_status.style('color: green')
                                    else:
                                        risk_ext_status.set_text('❌ ' + result.get('message', '失败'))
                                        risk_ext_status.style('color: red')

                                except Exception as ex:
                                    risk_ext_status.set_text(f'❌ 上传失败: {str(ex)}')
                                    risk_ext_status.style('color: red')

                            ui.upload(
                                label='选择风险金延伸（自动上传）',
                                on_upload=handle_risk_ext_upload,
                                auto_upload=True
                            ).classes('w-full')

                # ======================
                # 右侧：计算区
                # ======================
                with ui.column().classes('w-[340px] shrink-0'):

                    with ui.card().classes('w-full').style('background:#fafafa'):

                        ui.label('📊 数据计算').classes('text-h6')

                        def run_calc(btn, func, msg):
                            btn.disable()
                            btn.props('loading')

                            try:
                                func()
                                ui.notify(msg, type='positive')
                            except Exception as e:
                                ui.notify(f'❌ 计算失败: {e}', type='negative')

                            btn.props(remove='loading')
                            btn.enable()

                        # 按钮1
                        btn1 = ui.button(
                            '① 生成经济处理明细 v1'
                        ).classes('w-full bg-blue-500 text-white mt-2')

                        btn1.on_click(lambda: run_calc(
                            btn1,
                            engine.calculate_legal_economic_detail_v1,
                            '经济处理明细计算完成'
                        ))

                        # 按钮2
                        btn2 = ui.button(
                            '② 生成问责办基础数据'
                        ).classes('w-full bg-blue-500 text-white mt-2')

                        btn2.on_click(lambda: run_calc(
                            btn2,
                            engine.calculate_legal_accountability_base,
                            '问责办基础数据计算完成'
                        ))

                        # 按钮3
                        btn3 = ui.button(
                            '③ 计算人力风险金'
                        ).classes('w-full bg-blue-500 text-white mt-2')

                        btn3.on_click(lambda: run_calc(
                            btn3,
                            engine.calculate_hr_risk_fund,
                            '人力风险金计算完成'
                        ))

                        # 按钮4
                        btn4 = ui.button(
                            '④ 计算风险金延伸'
                        ).classes('w-full bg-blue-500 text-white mt-2')

                        btn4.on_click(lambda: run_calc(
                            btn4,
                            engine.calculate_hr_risk_fund_extended,
                            '风险金延伸计算完成'
                        ))

                        # 按钮5
                        btn5 = ui.button(
                            '⑤ 更新问责办风险'
                        ).classes('w-full bg-blue-500 text-white mt-2')

                        btn5.on_click(lambda: run_calc(
                            btn5,
                            engine.update_legal_accountability_risk,
                            '问责风险更新完成'
                        ))

                        ui.separator()

                        # ui.button(
                        #     '🚀 一键执行全部计算',
                        #     on_click=run_all
                        # ).classes('w-full bg-black text-white text-lg')

        # ========== Tab 5: 全量导出 ==========
        with ui.tab_panel('tab5'):
            ui.label('📥 导出所有6张表').classes('text-h6')

            def export_all():
                conn = get_conn()

                tables = [
                    ('hr_payroll', '人力工资表'),
                    ('hr_roster', '人力花名册'),
                    ('hr_risk_fund', '人力风险金'),
                    ('hr_risk_fund_extended', '人力风险金延伸'),
                    ('legal_economic_detail', '法律经济处理明细表'),
                    ('legal_accountability', '法律问责办台账'),
                ]

                with pd.ExcelWriter('全表数据导出.xlsx', engine='openpyxl') as writer:
                    for table_name, sheet_name in tables:
                        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
                        # 删除数据库自增ID
                        df = df.drop(columns=['id'], errors='ignore')
                        # 修改为中文表头
                        if table_name in COLUMN_MAP:
                            df.rename(columns=COLUMN_MAP[table_name], inplace=True)
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        # Excel 默认列宽很窄，可以自动调整：
                        for column in df.columns:
                            writer.sheets[sheet_name].column_dimensions[column].width = 18

                conn.close()
                ui.download('全表数据导出.xlsx')

            ui.button('📥 一键导出全部6张表', on_click=export_all).classes('bg-green-500 text-white w-full')

            ui.separator()

            with ui.row().classes('gap-2'):
                def export_payroll():
                    conn = get_conn()
                    df = pd.read_sql("SELECT * FROM hr_payroll", conn)
                    conn.close()
                    # 删除数据库自增ID
                    df = df.drop(columns=['id'], errors='ignore')
                    # 中文表头
                    df.rename(columns=COLUMN_MAP["hr_payroll"], inplace=True)
                    df.to_excel('人力工资表.xlsx', index=False)
                    ui.download('人力工资表.xlsx')

                def export_roster():
                    conn = get_conn()
                    df = pd.read_sql("SELECT * FROM hr_roster", conn)
                    conn.close()
                    # 删除数据库自增ID
                    df = df.drop(columns=['id'], errors='ignore')
                    # 中文表头
                    df.rename(columns=COLUMN_MAP["hr_roster"], inplace=True)
                    df.to_excel('人力花名册.xlsx', index=False)
                    ui.download('人力花名册.xlsx')

                def export_risk_fund():
                    conn = get_conn()
                    df = pd.read_sql("SELECT * FROM hr_risk_fund", conn)
                    conn.close()
                    # 删除数据库自增ID
                    df = df.drop(columns=['id'], errors='ignore')
                    # 中文表头
                    df.rename(columns=COLUMN_MAP["hr_risk_fund"], inplace=True)
                    df.to_excel('人力风险金.xlsx', index=False)
                    ui.download('人力风险金.xlsx')

                def export_risk_ext():
                    conn = get_conn()
                    df = pd.read_sql("SELECT * FROM hr_risk_fund_extended", conn)
                    conn.close()
                    # 删除数据库自增ID
                    df = df.drop(columns=['id'], errors='ignore')
                    # 中文表头
                    df.rename(columns=COLUMN_MAP["hr_risk_fund_extended"], inplace=True)
                    df.to_excel('人力风险金延伸.xlsx', index=False)
                    ui.download('人力风险金延伸.xlsx')

                def export_econ():
                    conn = get_conn()
                    df = pd.read_sql("SELECT * FROM legal_economic_detail", conn)
                    conn.close()
                    # 删除数据库自增ID
                    df = df.drop(columns=['id'], errors='ignore')
                    # 中文表头
                    df.rename(columns=COLUMN_MAP["legal_economic_detail"], inplace=True)
                    df.to_excel('法律经济处理明细表.xlsx', index=False)
                    ui.download('法律经济处理明细表.xlsx')

                def export_acct():
                    conn = get_conn()
                    df = pd.read_sql("SELECT * FROM legal_accountability", conn)
                    conn.close()
                    # 删除数据库自增ID
                    df = df.drop(columns=['id'], errors='ignore')
                    # 中文表头
                    df.rename(columns=COLUMN_MAP["legal_accountability"], inplace=True)
                    df.to_excel('法律问责办台账.xlsx', index=False)
                    ui.download('法律问责办台账.xlsx')

                ui.button('工资表', on_click=export_payroll).classes('bg-blue-500 text-white flex-1')
                ui.button('花名册', on_click=export_roster).classes('bg-blue-500 text-white flex-1')
                ui.button('风险金', on_click=export_risk_fund).classes('bg-blue-500 text-white flex-1')
                ui.button('风险金延伸', on_click=export_risk_ext).classes('bg-blue-500 text-white flex-1')
                ui.button('经济处理', on_click=export_econ).classes('bg-blue-500 text-white flex-1')
                ui.button('问责办台账', on_click=export_acct).classes('bg-blue-500 text-white flex-1')

        # ========== Tab 6: 系统信息 ==========
        with ui.tab_panel('tab6'):
            ui.markdown('''
            ## 📋 系统说明

            这是一个**6表协作系统**，用于法律部门和人力资源部门的财务合规管理。

            ### 🔄 完整工作流程

            **第1阶段：基础导入**
            - 人力部导入：工资表 + 花名册

            

            **第2阶段：法律部处理**
            - 法律部下载经济处理明细表(v1)
            - 手工修改：税前、税后
            - 重新上传(v2)
            
            **第3阶段：其他导入**
            - 人力导入：风险金延伸初始数据
            - 法律导入：问责办台账初始数据

            **第5阶段：最终计算**
            - 系统自动计算所有派生字段

            ### 📊 6张表说明

            | # | 表名 | 来源 | 主键 | 自动计算字段 |
            |---|------|------|------|------------|
            | 1 | 人力工资表 | 人力导入 | 日期+员工号 | ❌ 无 |
            | 2 | 人力花名册 | 人力导入 | 员工号 | ❌ 无 |
            | 3 | 人力风险金 | 自动计算 | 员工号+年份 | ✅ 12个月+累计 |
            | 4 | 人力风险金延伸 | 人力导入+计算 | 日期+员工号 | ✅ 多年份余额+返还 |
            | 5 | 法律经济处理明细 | 法律导入(二次) | 日期+员工号+文号 | ✅ 核算金额 |
            | 6 | 法律问责办台账 | 法律导入+计算 | 日期+员工号 | ✅ 执行金额+累计 |

            ### ⚙️ 计算顺序（重要！）

            1. ✅ 经济处理明细v1（基于工资表）
            2. ✅ 问责办台账基础数据（基于工资表+花名册）
            3. ✅ 人力风险金（基于工资表）
            4. ✅ 人力风险金延伸（基于风险金+问责台账）
            5. ✅ 问责办台账（基于风险金延伸）

            ### 🔗 表间关联规则

            人力风险金延伸重要计算逻辑：主键--日期+员工号
            需要关联和计算的列如下：
            
            N-4年余额=取自人力风险金--N-4年累计延期薪酬余额
            N-3年余额=取自人力风险金--N-3年累计延期薪酬余额	
            N-2年余额=取自人力风险金--N-2年累计延期薪酬余额
            
            余额合计=N-4年余额+N-3年余额+N-2年余额
            
            N-4年待返还金额=N-4年余额
            
            N-4年问责办扣减=min(N-4年待返还金额，问责办提供税前)
            
            N-4年实际返还金额=N-4年待返还金额-N-4年问责办扣减-N-4年纪委办缓发-N-4年授信扣减-N-4年二分缓发-N-4年其他
            
            
            N-3年待返还金额
            =N-3年余额/0.6667*0.3333
            
            N-3年问责办扣减
            =min （N-3年待返还金额，（问责办提供税前-N-4年问责办扣减））
            
            N-3年实际返还金额
            =N-3年待返还金额-N-3年问责办扣减	-N-3年纪委办缓发	-N-3年授信扣减	-N-3年二分缓发-	N-3年其他
            
            N-2年待返还金额=N-2年余额*0.3333
            
            N-2年问责办扣减=min(N-2年待返还金额,(问责办提供税前-N-4年问责办扣减-N-3年问责办扣减))
            
            N-2年实际返还金额=N-2年待返还金额-N-2年问责办扣减	-N-2年纪委办缓发-	N-2年授信扣减-	N-2年二分缓发-	N-2年其他
            
            
            
            当年返还风险金合计=N-2年实际返还金额+N-3年实际返还金额+N-4年实际返还金额
            
            
            问责办实际执行税前=N-4年问责办扣减+N-3年问责办扣减+N-2年问责办扣减
            
            
            问责办实际执行税后=取工资表列名--问责     
            关联条件：日期+员工号
            
            
            问责办提供税前=取 法律问责办台账列名--税前待执行金额剩余 
            提取规则----执行日期人力用--这个日期最大的那条对应的税前待执行金额剩余  
            关联条件：员工号
            
            问责办提供税后=取 法律问责办台账列名--税后待执行金额剩余 
            提取规则---执行日期人力用--这个日期最大的那条对应的税后待执行金额剩余 
             关联条件：员工号
            
            文号：取 法律问责办台账列名--文号
            执行日期人力用--这个日期最大的那条对应的文号
             关联条件：员工号
            
            N-4年执行后余额=N-4年余额-N-4年问责办扣减-N-4年授信扣减-N-4年其他
            N-3年执行后余额=	N-3年余额-N-3年问责办扣减-N-3年授信扣减-N-3年其他
            N-2年执行后余额=	N-2年余额-N-2年问责办扣减-N-2年授信扣减-N-2年其他
            
            累计余额=取自人力风险金--累计延期薪酬余额
            关联条件：员工号+年份
            
            累计延期薪酬余额-当年返还风险金合计-问责办实际执行税前-N-4年授信扣减-N-3年授信扣减
            -N-2年授信扣减-N-4年其他-N-3年其他-N-2年其他

            ### ⚠️ 注意事项

            1. **日期格式**：所有日期必须是 `YYYYMM` 格式（如 202501）
            2. **关联失败**：找不到关联数据时，相关字段留空
            3. **累计计算**：按执行日期从小到大累计求和
            

            
            ''')


# ==================== 应用启动 ====================

if __name__ == '__main__':
    def open_browser():
        import time
        time.sleep(1)
        webbrowser.open('http://127.0.0.1:25001')


    print("=" * 60)
    print("🚀 6表协作系统启动中...")
    print("📍 地址: http://127.0.0.1:25001")
    print("=" * 60)
    print()

    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    ui.run(
        host='0.0.0.0',
        port=25001,
        reload=False,
        show=False,
        storage_secret='hfbank_secret_123456'  # ✅ 随便写一个字符串（建议复杂点）
    )