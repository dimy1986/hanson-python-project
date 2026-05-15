# -*- coding: utf-8 -*-
"""
表格检查工具
功能：
1. 循环读取 d:/待检查文件夹 下的所有Excel表格
2. 根据三个规则进行检查
3. 输出结果到 检查结果.xlsx
"""

import os
import pandas as pd
from datetime import datetime
from pathlib import Path
import traceback

# 检查结果存储
check_results = []


def parse_date_range(date_str):
    """
    解析日期范围，如 '2023.8-2026.8'
    返回 (start_year, start_month, end_year, end_month)
    """
    if not date_str or pd.isna(date_str):
        return None
    
    try:
        date_str = str(date_str).strip()
        # 分割开始和结束日期
        parts = date_str.split('-')
        if len(parts) != 2:
            return None
        
        start_part = parts[0].strip()
        end_part = parts[1].strip()
        
        # 解析开始日期
        start_dates = start_part.split('.')
        if len(start_dates) != 2:
            return None
        start_year = int(start_dates[0])
        start_month = int(start_dates[1])
        
        # 解析结束日期
        end_dates = end_part.split('.')
        if len(end_dates) != 2:
            return None
        end_year = int(end_dates[0])
        end_month = int(end_dates[1])
        
        return (start_year, start_month, end_year, end_month)
    except Exception as e:
        print(f"日期解析错误: {date_str}, 错误: {e}")
        return None


def is_year_in_range(year, date_range):
    """
    判断指定年份是否在有效期范围内
    date_range: (start_year, start_month, end_year, end_month)
    """
    if not date_range:
        return False
    
    start_year, start_month, end_year, end_month = date_range
    
    # 如果只是年份，判断是否在[start_year, end_year]范围内
    return start_year <= year <= end_year


def check_rule_1(row):
    """
    规则1: 2025年度是否需要参加测评
    - 判断条件: 持有合格证有效期字段值
    - 如果2025在有效期范围内 → 否（不需要参加）
    - 如果2025不在有效期范围内 → 是（需要参加）
    - 检查: 如果与"2025年度是否需要参加测评"字段值不一致，返回错误
    """
    errors = []
    
    # 查找相关字段（尝试多种可能的列名）
    valid_period_col = None
    need_test_col = None
    
    for col in row.index:
        col_str = str(col).lower()
        if '持有合格证' in col or '有效期' in col:
            valid_period_col = col
        if '2025年度是否需要参加测评' in col:
            need_test_col = col
    
    if valid_period_col is None or need_test_col is None:
        return errors
    
    valid_period_value = row[valid_period_col]
    need_test_value = row[need_test_col]
    
    if pd.isna(valid_period_value) or pd.isna(need_test_value):
        return errors
    
    # 解析有效期
    date_range = parse_date_range(valid_period_value)
    if date_range is None:
        return errors
    
    # 判断2025是否在范围内
    is_in_range = is_year_in_range(2025, date_range)
    
    # 如果在范围内，则不需要参加测评 → 应该为"否"
    # 如果不在范围内，则需要参加测评 → 应该为"是"
    expected_value = "否" if is_in_range else "是"
    
    # 转换输入值为标准格式
    actual_value = str(need_test_value).strip()
    
    if actual_value != expected_value:
        errors.append({
            'type': '规则1',
            'field': '2025年度是否需要参加测评',
            'expected': expected_value,
            'actual': actual_value,
            'message': f"2025年度是否需要参加测评值不对，应为'{expected_value}'，实际为'{actual_value}'"
        })
    
    return errors


def check_rule_2(row):
    """
    规则2: 第三方测评培训时间
    - 检查条件: 
      - 若培训时间在持有合格证有效期开始日期之前且为同一年，则不返回（正常）
      - 否则返回错误
    """
    errors = []
    
    # 查找相关字段
    valid_period_col = None
    training_time_col = None
    
    for col in row.index:
        col_str = str(col).lower()
        if '持有合格证' in col or '有效期' in col:
            valid_period_col = col
        if '第三方测评培训时间' in col or '培训时间' in col:
            training_time_col = col
    
    if valid_period_col is None or training_time_col is None:
        return errors
    
    valid_period_value = row[valid_period_col]
    training_time_value = row[training_time_col]
    
    if pd.isna(valid_period_value) or pd.isna(training_time_value):
        return errors
    
    # 解析有效期
    date_range = parse_date_range(valid_period_value)
    if date_range is None:
        return errors
    
    start_year = date_range[0]
    start_month = date_range[1]
    
    # 解析培训时间（尝试识别年份和月份）
    training_str = str(training_time_value).strip()
    
    try:
        # 尝试多种格式
        training_parts = training_str.replace('/', '.').split('.')
        if len(training_parts) >= 2:
            training_year = int(training_parts[0])
            training_month = int(training_parts[1])
            
            # 检查: 培训时间应该在有效期开始日期之前且为同一年
            if training_year == start_year and training_month < start_month:
                # 正常情况，不返回错误
                pass
            else:
                # 异常情况
                errors.append({
                    'type': '规则2',
                    'field': '第三方测评培训时间',
                    'expected': f'在 {start_year}.{start_month} 之前的同一年',
                    'actual': training_str,
                    'message': f"第三方测评培训时间不对，应在持有合格证有效期开始日期({start_year}.{start_month})之前的同一年"
                })
    except Exception as e:
        # 如果无法解析，则记录错误
        errors.append({
            'type': '规则2',
            'field': '第三方测评培训时间',
            'expected': '有效的日期格式',
            'actual': training_str,
            'message': f"第三方测评培训时间格式无法识别: {training_str}"
        })
    
    return errors


def check_rule_3(row):
    """
    规则3: 考试成绩
    - 检查条件: 如果成绩 < 90，则返回错误
    """
    errors = []
    
    # 查找考试成绩字段
    score_col = None
    
    for col in row.index:
        col_str = str(col).lower()
        if '考试成绩' in col or '成绩' in col:
            score_col = col
            break
    
    if score_col is None:
        return errors
    
    score_value = row[score_col]
    
    if pd.isna(score_value):
        return errors
    
    try:
        score = float(score_value)
        if score < 90:
            errors.append({
                'type': '规则3',
                'field': '考试成绩',
                'expected': '≥90',
                'actual': score,
                'message': f"成绩低于90，实际成绩为 {score}"
            })
    except ValueError:
        errors.append({
            'type': '规则3',
            'field': '考试成绩',
            'expected': '有效的数字',
            'actual': score_value,
            'message': f"考试成绩无法转换为数字: {score_value}"
        })
    
    return errors


def check_single_file(file_path):
    """
    检查单个Excel文件
    """
    file_results = []
    
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 遍历每一行
        for idx, row in df.iterrows():
            row_errors = []
            
            # 执行三个检查规则
            row_errors.extend(check_rule_1(row))
            row_errors.extend(check_rule_2(row))
            row_errors.extend(check_rule_3(row))
            
            # 如果有错误，记录
            if row_errors:
                for error in row_errors:
                    file_results.append({
                        '文件名': os.path.basename(file_path),
                        '行号': idx + 2,  # +2是因为索引从0开始，且第一行是表头
                        '检查项': error['type'],
                        '字段名': error['field'],
                        '期望值': error['expected'],
                        '实际值': error['actual'],
                        '错误信息': error['message'],
                        '检查时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
    
    except Exception as e:
        file_results.append({
            '文件名': os.path.basename(file_path),
            '行号': '',
            '检查项': '文件读取',
            '字段名': '',
            '期望值': '',
            '实际值': '',
            '错误信息': f"文件读取失败: {str(e)}",
            '检查时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return file_results


def main():
    """
    主程序：
    1. 遍历 d:/待检查文件夹 下的所有Excel文件
    2. 对每个文件执行检查
    3. 将结果输出到 检查结果.xlsx
    """
    
    # 待检查文件夹路径
    check_folder = r'd:\待检查文件夹'
    
    # 确保文件夹存在
    if not os.path.exists(check_folder):
        print(f"❌ 文件夹不存在: {check_folder}")
        os.makedirs(check_folder, exist_ok=True)
        print(f"✅ 已创建文件夹: {check_folder}")
        return
    
    # 收集所有Excel文件
    excel_files = []
    for file in os.listdir(check_folder):
        if file.endswith(('.xlsx', '.xls')):
            file_path = os.path.join(check_folder, file)
            excel_files.append(file_path)
    
    if not excel_files:
        print(f"⚠️ 文件夹中没有找到Excel文件: {check_folder}")
        return
    
    print(f"✅ 找到 {len(excel_files)} 个Excel文件，开始检查...\n")
    
    # 遍历每个文件进行检查
    all_errors = []
    for file_path in excel_files:
        print(f"📄 检查文件: {os.path.basename(file_path)}")
        file_errors = check_single_file(file_path)
        all_errors.extend(file_errors)
        if file_errors:
            print(f"   ⚠️ 发现 {len(file_errors)} 个错误")
        else:
            print(f"   ✅ 检查完成，无错误")
    
    # 输出结果到Excel
    output_file = r'd:\检查结果.xlsx'
    
    if all_errors:
        # 将结果转换为DataFrame
        result_df = pd.DataFrame(all_errors)
        
        # 输出到Excel
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            result_df.to_excel(writer, sheet_name='检查结果', index=False)
            
            # 自动调整列宽
            worksheet = writer.sheets['检查结果']
            for idx, col in enumerate(result_df.columns, 1):
                max_length = max(
                    result_df[col].astype(str).apply(len).max(),
                    len(col)
                )
                worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 50)
        
        print(f"\n✅ 检查完成！发现 {len(all_errors)} 个错误")
        print(f"📊 结果已保存到: {output_file}")
    else:
        # 创建空的结果文件表示检查完成
        result_df = pd.DataFrame({
            '文件名': ['检查完成'],
            '行号': [''],
            '检查项': [''],
            '字段名': [''],
            '期望值': [''],
            '实际值': [''],
            '错误信息': ['所有文件均检查通过，无错误'],
            '检查时间': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        })
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            result_df.to_excel(writer, sheet_name='检查结果', index=False)
        
        print(f"\n✅ 检查完成！所有文件均检查通过，无错误")
        print(f"📊 结果已保存到: {output_file}")


if __name__ == '__main__':
    print("=" * 60)
    print("📋 表格检查工具")
    print("=" * 60)
    print()
    
    main()
    
    print("\n✨ 程序执行完毕")
