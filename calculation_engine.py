# -*- coding: utf-8 -*-
"""
计算引擎：所有6张表的自动计算逻辑
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, List, Tuple


class CalculationEngine:
    def __init__(self, db_path: str = 'data.db'):
        self.db_path = db_path

    def get_conn(self):
        return sqlite3.connect(self.db_path)

    # ==================== 步骤1: 人力风险金计算 ====================

    def calculate_hr_risk_fund(self):

        conn = self.get_conn()
        cursor = conn.cursor()

        try:

            # 获取风险金表所有员工年份
            cursor.execute("""
                SELECT employee_id, year
                FROM hr_risk_fund
                ORDER BY employee_id, year
            """)

            rows = cursor.fetchall()

            for employee_id, year in rows:

                # 一次性取全年工资数据
                cursor.execute("""
                    SELECT substr(date,5,2) as month, deferred_salary
                    FROM hr_payroll
                    WHERE employee_id = ?
                    AND substr(date,1,4) = ?
                """, (employee_id, str(year)))

                payroll_data = cursor.fetchall()

                monthly = {f"month_{i:02d}": 0 for i in range(1, 13)}

                for month, value in payroll_data:
                    key = f"month_{month}"
                    monthly[key] = value or 0

                # 当年累计
                annual_total = sum(monthly.values())

                # 历史累计
                cursor.execute("""
                    SELECT COALESCE(SUM(annual_deferred),0)
                    FROM hr_risk_fund
                    WHERE employee_id = ?
                    AND year < ?
                """, (employee_id, year))

                prev = cursor.fetchone()[0]

                cumulative = prev + annual_total

                # 更新
                cursor.execute("""
                    UPDATE hr_risk_fund
                    SET
                        month_01=?,
                        month_02=?,
                        month_03=?,
                        month_04=?,
                        month_05=?,
                        month_06=?,
                        month_07=?,
                        month_08=?,
                        month_09=?,
                        month_10=?,
                        month_11=?,
                        month_12=?,
                        annual_deferred=?,
                        cumulative_deferred=?,
                        updated_at=?,
                        calc_flag = 1
                    WHERE employee_id=? AND year=?
                """, (

                    monthly["month_01"],
                    monthly["month_02"],
                    monthly["month_03"],
                    monthly["month_04"],
                    monthly["month_05"],
                    monthly["month_06"],
                    monthly["month_07"],
                    monthly["month_08"],
                    monthly["month_09"],
                    monthly["month_10"],
                    monthly["month_11"],
                    monthly["month_12"],

                    annual_total,
                    cumulative,
                    datetime.now(),
                    employee_id,
                    year
                ))

            conn.commit()
            print("✅ 人力风险金计算完成")
            return True

        except Exception as e:
            print(f"❌ 人力风险金计算失败: {e}")
            conn.rollback()
            return False

        finally:
            conn.close()

    # ==================== 步骤2: 法律经济处理明细表（首次）====================

    def calculate_legal_economic_detail_v1(self):
        """
        首次导入：计算核算金额
        核算金额 = (合计绩效工资按年份汇总 / 12) × 系数

        关联条件：日期+员工号（年份来自salary_year）
        """
        conn = self.get_conn()
        cursor = conn.cursor()

        try:
            # 获取所有经济处理明细表v1记录
            cursor.execute("""
                SELECT id, employee_id, salary_year, coefficient
                FROM legal_economic_detail
                where calc_flag = 0
                ORDER BY id
            """)

            records = cursor.fetchall()

            for record_id, employee_id, salary_year, coefficient in records:
                print("处理:", record_id, employee_id, salary_year, coefficient)

                cursor.execute("""
                    SELECT SUM(total_perf)
                    FROM hr_payroll
                    WHERE employee_id = ?
                    AND substr(date,1,4) = ?
                """, (employee_id, str(salary_year)))

                result = cursor.fetchone()
                total_taxable = result[0] if result and result[0] else 0

                print("合计绩效工资:", total_taxable)

                accounting_amount = round((total_taxable / 12) * coefficient,2)

                print("核算金额:", accounting_amount)

                cursor.execute("""
                    UPDATE legal_economic_detail
                    SET accounting_amount=?,status='待下载',updated_at=?,
                    calc_flag=1
                    WHERE id=?
                """, (accounting_amount, datetime.now(), record_id))

            conn.commit()
            print("✅ 法律经济处理明细表(v1)计算完成")
            return True

        except Exception as e:
            print(f"❌ 经济处理明细表计算失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # ==================== 步骤3: 法律台账基础计算====================
    def calculate_legal_accountability_base(self):

        conn = self.get_conn()
        cursor = conn.cursor()

        try:

            sql_expand="""INSERT INTO legal_accountability (
                        sequence_no, branch, employee_id, employee_name,
                        original_organization, original_position_category, original_position_title,
                        current_organization, current_position_category, current_position_title,
                        employee_status, violation_source, violation_attribution, violation_description,
                        violation_discovery_date, accountability_project, doc_number,
                        accountability_authority, decision_body, issue_date, handling_basis,
                        discipline_type, tax_pre, tax_post, total_economic,
                        main_pay_tax_pre, main_pay_tax_post, exec_date_legal, exec_date_hr,
                        criticism, remark, conference
                    )
                    SELECT
                        la.sequence_no,
                        la.branch,
                        la.employee_id,
                        la.employee_name,
                        la.original_organization,
                        la.original_position_category,
                        la.original_position_title,
                        la.current_organization,
                        la.current_position_category,
                        la.current_position_title,
                        la.employee_status,
                        la.violation_source,
                        la.violation_attribution,
                        la.violation_description,
                        la.violation_discovery_date,
                        la.accountability_project,
                        la.doc_number,
                        la.accountability_authority,
                        la.decision_body,
                        la.issue_date,
                        la.handling_basis,
                        la.discipline_type,
                        la.tax_pre,
                        la.tax_post,
                        la.total_economic,
                        la.main_pay_tax_pre,
                        la.main_pay_tax_post,
                        la.exec_date_legal,
                        p.date,      
                        la.criticism,
                        la.remark,
                        la.conference
                    FROM legal_accountability la
                    JOIN hr_payroll p
                        ON la.employee_id = p.employee_id
                       AND la.doc_number = p.doc_number
                    WHERE p.tax_pre_accountability_perf IS NOT NULL
                      AND la.exec_date_hr is null
                      AND NOT EXISTS (
                            SELECT 1
                            FROM legal_accountability t
                            WHERE t.employee_id = la.employee_id
                              AND t.doc_number = la.doc_number
                              AND t.exec_date_hr = p.date
                      );"""
            sql_delete="""DELETE FROM legal_accountability
                        WHERE exec_date_hr is null
                        AND EXISTS (
                            SELECT 1
                            FROM hr_payroll p
                            WHERE p.employee_id = legal_accountability.employee_id
                              AND p.doc_number = legal_accountability.doc_number
                              AND p.tax_pre_accountability_perf IS NOT NULL
                        );"""
            # 同步工资日期,复制所有字段
            cursor.execute(sql_expand)

            #删除扩展后多余的null

            cursor.execute(sql_delete)

            conn.commit()
            # ================= 工资表一次性读取 =================
            cursor.execute("""
                   SELECT employee_id, date, tax_pre_accountability_perf, accountability
                   FROM hr_payroll
                   WHERE tax_pre_accountability_perf IS NOT NULL
                   """)

            payroll_map = {
                (r[0], r[1]): {
                    "perf": r[2] or 0,# tax_pre_accountability_perf  税前问责扣减绩效
                    "acct": r[3] or 0 # accountability  问责
                }
                for r in cursor.fetchall()
            }

            # ================= 获取台账数据 =================
            cursor.execute("""
                   SELECT
                       id,
                       employee_id,
                       exec_date_hr,
                       tax_pre,
                       tax_post,
                       main_pay_tax_pre,
                       main_pay_tax_post,
                       total_economic
                   FROM legal_accountability where calc_flag=0
                   ORDER BY employee_id,doc_number, exec_date_hr
                   """)

            rows = cursor.fetchall()

            # ================= 累计变量 =================
            perf_cumulative = {}

            for row in rows:

                (
                    rid,
                    emp,
                    date,
                    tax_pre,   #"税前",
                    tax_post,  #"税后",
                    main_pre,  #"主要缴纳金额税前",
                    main_post, # "主要缴纳金额税后",
                    total_econ  #"合计经济处理金额",
                ) = row

                tax_pre = tax_pre or 0
                tax_post = tax_post or 0
                main_pre = main_pre or 0
                main_post = main_post or 0
                total_econ = total_econ or 0

                # 花名册政治面貌
                cursor.execute("""
                       SELECT political_status
                       FROM hr_roster
                       WHERE employee_id=?
                       """, (emp,))

                r = cursor.fetchone()
                political = r[0] if r else None

                # 工资数据
                pay = payroll_map.get((emp, date), {})
                #扣减当期绩效=取自人力工资表列名--税前问责扣减绩效
                perf = pay.get("perf", 0)
                #税后问责=取自人力工资表列名--问责
                risk_deduction = pay.get("acct", 0)

                # ================= 累计绩效 =================
                if emp not in perf_cumulative:
                    perf_cumulative[emp] = 0

                perf_cumulative[emp] += perf
                cumulative_performance = perf_cumulative[emp]  #累计执行绩效金额

                # ================= 原逻辑计算 =================
                #税前执行金额=主要缴纳金额税前+扣减当期绩效+扣减风险金
                tax_pre_exec = main_pre + perf
                #税后执行金额=主要缴纳金额税后+税后问责
                tax_post_exec = main_post+risk_deduction
                #税前待执行金额剩余	=税前-税前执行金额
                tax_pre_pending = tax_pre - tax_pre_exec
                #税后待执行剩余金额	=税后-税后执行金额
                tax_post_pending = tax_post - tax_post_exec
                #税前加税后执行金额	=税前执行金额+税后执行金额
                exec_total = tax_pre_exec + tax_post_exec
                # 未执行合计金额=合计经济处理金额-税前加税后执行金额-主要缴纳金额税前-主要缴纳金额税后
                unexec_total = total_econ - exec_total -main_pre -main_post

                # ================= 更新 =================
                cursor.execute("""
                       UPDATE legal_accountability
                       SET
                           political_status=?,
                           performance_adjustment=?,
                           risk_deduction=?,
                           cumulative_performance=?,
                           accountability_tax_post=NULL,
                           cumulative_risk=NULL,
                           tax_pre_exec=?,
                           tax_post_exec=?,
                           tax_pre_pending=?,
                           tax_post_pending=?,
                           exec_total=?,
                           unexec_total=?,
                           updated_at=?,
                           calc_flag=1
                       WHERE id=?
                       """, (
                    political,
                    perf,
                    risk_deduction,
                    cumulative_performance,
                    tax_pre_exec,
                    tax_post_exec,
                    tax_pre_pending,
                    tax_post_pending,
                    exec_total,
                    unexec_total,
                    datetime.now(),
                    rid
                ))

            conn.commit()

            print("法律基础计算完成")

        finally:
            conn.close()



    # ==================== 步骤4: 人力风险金延伸 ====================

    def calculate_hr_risk_fund_extended(self):

        conn = self.get_conn()
        cursor = conn.cursor()

        try:

            cursor.execute("""
            SELECT id,employee_id,date,
                   n4_committee_defer,n4_credit_deduct,n4_bifurcated_defer,n4_other,
                   n3_committee_defer,n3_credit_deduct,n3_bifurcated_defer,n3_other,
                   n2_committee_defer,n2_credit_deduct,n2_bifurcated_defer,n2_other
            FROM hr_risk_fund_extended where calc_flag=0
            ORDER BY employee_id,date
            """)

            rows = cursor.fetchall()

            for row in rows:

                (rid, emp, date,
                 n4_cd, n4_cr, n4_bi, n4_ot,
                 n3_cd, n3_cr, n3_bi, n3_ot,
                 n2_cd, n2_cr, n2_bi, n2_ot) = row

                year = int(date[:4])

                years = [year - 4, year - 3, year - 2]

                risks = {}

                for y in years:
                    cursor.execute("""
                    SELECT cumulative_deferred
                    FROM hr_risk_fund
                    WHERE employee_id=? AND year=? 
                    """, (emp, y))

                    r = cursor.fetchone()

                    risks[y] = r[0] if r and r[0] else 0

                n4_balance = risks[year - 4]
                n3_balance = risks[year - 3]
                n2_balance = risks[year - 2]

                balance_total = n4_balance + n3_balance + n2_balance

                cursor.execute("""
                SELECT tax_pre_pending,tax_post_pending,doc_number
                FROM legal_accountability
                WHERE employee_id=?
                ORDER BY exec_date_hr DESC
                LIMIT 1
                """, (emp,))

                r = cursor.fetchone()

                if r:
                    acct_pre = r[0] or 0
                    acct_post = r[1] or 0
                    doc = r[2]
                else:
                    acct_pre = 0
                    acct_post = 0
                    doc = ""

                # =================
                # N4
                # =================

                n4_repay_pending = n4_balance

                n4_deduct = min(n4_repay_pending, acct_pre)

                n4_actual = (
                        n4_repay_pending
                        - n4_deduct
                        - (n4_cd or 0)
                        - (n4_cr or 0)
                        - (n4_bi or 0)
                        - (n4_ot or 0)
                )

                remain = acct_pre - n4_deduct

                # =================
                # N3
                # =================

                n3_repay_pending = n3_balance / 0.6667 * 0.3333

                n3_deduct = min(n3_repay_pending, remain)

                remain -= n3_deduct

                n3_actual = (
                        n3_repay_pending
                        - n3_deduct
                        - (n3_cd or 0)
                        - (n3_cr or 0)
                        - (n3_bi or 0)
                        - (n3_ot or 0)
                )

                # =================
                # N2
                # =================

                n2_repay_pending = n2_balance * 0.3333

                n2_deduct = min(n2_repay_pending, remain)

                n2_actual = (
                        n2_repay_pending
                        - n2_deduct
                        - (n2_cd or 0)
                        - (n2_cr or 0)
                        - (n2_bi or 0)
                        - (n2_ot or 0)
                )
                #计算问责办实际执行税后=取工资表列名--问责
                cursor.execute("""
                SELECT SUM(accountability)
                FROM hr_payroll
                WHERE employee_id=?
                AND substr(date,1,4)=?
                """, (emp, str(year)))

                r = cursor.fetchone()

                acct_actual_post = r[0] if r and r[0] else 0

                # =================
                # 汇总
                # =================

                annual_repay_total = n4_actual + n3_actual + n2_actual

                acct_actual_pre = n4_deduct + n3_deduct + n2_deduct

                # =================
                # 执行后余额
                # =================

                n4_after = n4_balance - n4_deduct - (n4_cr or 0) - (n4_ot or 0)

                n3_after = n3_balance - n3_deduct - (n3_cr or 0) - (n3_ot or 0)

                n2_after = n2_balance - n2_deduct - (n2_cr or 0) - (n2_ot or 0)

                # =================
                # 累计余额
                # =================

                cursor.execute("""
                SELECT cumulative_deferred
                FROM hr_risk_fund
                WHERE employee_id=? AND year=?
                """, (emp, year))

                r = cursor.fetchone()

                cumulative = r[0] if r else 0

                final_balance = (
                        cumulative
                        - annual_repay_total
                        - acct_actual_pre
                        - (n4_cr or 0) - (n3_cr or 0) - (n2_cr or 0)
                        - (n4_ot or 0) - (n3_ot or 0) - (n2_ot or 0)
                )

                cursor.execute("""
                UPDATE hr_risk_fund_extended
                SET
                n4_balance=?,n3_balance=?,n2_balance=?,
                balance_total=?,

                n4_repay_pending=?,n3_repay_pending=?,n2_repay_pending=?,

                n4_accountability_deduct=?,n3_accountability_deduct=?,n2_accountability_deduct=?,

                n4_actual_repay=?,n3_actual_repay=?,n2_actual_repay=?,

                annual_repay_total=?,

                accountability_actual_tax_pre=?,
                accountability_actual_tax_post=?,
                accountability_provide_tax_pre=?,
                accountability_provide_tax_post=?,
                doc_number=?,

                n4_after_exec_balance=?,
                n3_after_exec_balance=?,
                n2_after_exec_balance=?,
                calc_flag=1,
                final_balance=?,
                updated_at=?

                WHERE id=?
                """, (

                    n4_balance, n3_balance, n2_balance,
                    balance_total,

                    n4_repay_pending, n3_repay_pending, n2_repay_pending,

                    n4_deduct, n3_deduct, n2_deduct,

                    n4_actual, n3_actual, n2_actual,

                    annual_repay_total,

                    acct_actual_pre,
                    acct_actual_post,
                    acct_pre,
                    acct_post,
                    doc,

                    n4_after, n3_after, n2_after,

                    final_balance,
                    datetime.now(),

                    rid
                ))

            conn.commit()

            print("风险金延伸计算完成")

        finally:

            conn.close()



    # ==================== 步骤5: 法律台账回写风险金 ====================
    #更新字段为  扣减风险金   税前执行金额 （在步骤三中只计算了 主要缴纳金额税前+扣减当期绩效）  累计执行风险金金额
    def update_legal_accountability_risk(self):

        conn = self.get_conn()
        cursor = conn.cursor()

        try:

            # ================= 1 风险金映射 =================
            cursor.execute("""
                SELECT employee_id, exec_date, accountability_actual_tax_pre
                FROM hr_risk_fund_extended
                WHERE accountability_actual_tax_pre IS NOT NULL
            """)

            risk_map = {
                (r[0], r[1]): r[2] or 0
                for r in cursor.fetchall()
            }

            # ================= 2 获取法律台账 =================
            cursor.execute("""
                SELECT id,
                       employee_id,
                       exec_date_hr,
                       main_pay_tax_pre,
                       performance_adjustment,
                       cumulative_risk
                FROM legal_accountability
                ORDER BY employee_id, exec_date_hr
            """)

            rows = cursor.fetchall()

            # ================= 3 累计计算 =================
            risk_cumulative = {}

            for row in rows:

                rid = row[0]
                emp = row[1]
                date = row[2]

                main_amount = row[3] or 0
                perf = row[4] or 0

                # ================= 核心1：扣减风险金 =================
                risk = risk_map.get((emp, date), 0)
                if risk == 0:
                    print(f"未匹配到风险金: {emp} {date}")

                # ===== 累计（只按员工）=====
                if emp not in risk_cumulative:
                    risk_cumulative[emp] = 0

                risk_cumulative[emp] += risk
                cumulative_risk = risk_cumulative[emp]

                # ================= 核心3：税前执行金额 =================
                tax_pre_exec = main_amount + perf + risk

                # ================= 更新 =================
                cursor.execute("""
                    UPDATE legal_accountability
                    SET
                        accountability_tax_post = ?,   -- 扣减风险金
                        tax_pre_exec = ?,              -- 税前执行金额
                        cumulative_risk = ?,           -- 累计执行风险金金额
                        updated_at = ?
                    WHERE id = ?
                """, (
                    risk,
                    tax_pre_exec,
                    cumulative_risk,
                    datetime.now(),
                    rid
                ))

            conn.commit()

            print("法律台账风险金更新完成")

        finally:
            conn.close()

    # ==================== 触发所有计算 ====================

    def recalculate_all(self):
        """
        按顺序重新计算所有派生字段
        触发顺序很重要！
        """
        print("\n🔄 开始全量计算...")

        # 步骤1: 人力风险金（基于工资表）
        self.calculate_hr_risk_fund()

        # 步骤2: 经济处理明细表v1（基于工资表）
        self.calculate_legal_economic_detail_v1()

        # 步骤3: 人力风险金延伸（基于风险金+问责台账）
        self.calculate_hr_risk_fund_extended()

        # 步骤4: 问责办台账（基于工资表+花名册+风险金延伸）
        self.calculate_legal_accountability()

        print("\n✅ 全量计算完成！\n")