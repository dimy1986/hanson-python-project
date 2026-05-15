# -*- coding: utf-8 -*-
"""
表格检查工具 v3 - 精确单元格定位
功能：
1. 循环读取 d:/待检查文件夹 下的所有Excel表格
2. 根据指定的单元格位置读取数据
3. 按照三个规则进行检查
4. 输出结果到 待检查文件夹/检查结果.xlsx

字段位置（固定）：
- E5: "2025年度是否需要参加测评" 标签
- H5: 2025年度是否需要参加测评 的字段值 (是/否)
- F6: "持有合格证有效期" 标签
- H6: 持有合格证有效期 的字段值 (如 2023.8-2026.8)
- B9: "第三方测评培训时间" 标签
- D9: 第三方测评培训时间 的字段值 (如 2023/6/22)
- H19: "考试成绩" 标签
- H列 19行以下: 考试成绩的具体数值
"""

import os
import pandas as pd
from datetime import datetime
import traceback
from openpyxl import load_workbook


def get_cell_value(ws, cell_address):
    """获取指定单元格的值"""
    try:
        cell = ws[cell_address]
        return str(cell.value).strip() if cell.value else None
    except Exception as e:
        print(f"      ❌ 读取单元格 {cell_address} 出错: {e}")
        return None


def parse_date_range(date_str):
    """
    解析日期范围，如 '2023.8-2026.8' 或 '2023/8-2026/8'
    返回 (start_year, start_month, end_year, end_month)
    """
    if not date_str:
        return None
    
    try:
        date_str = str(date_str).strip()
        # 替换不同的分隔符
        date_str = date_str.replace('/', '.').replace('～', '-').replace('~', '-')
        
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
        print(f"      ❌ 日期解析错误: {date_str}")
        return None


def is_year_in_range(year, date_range):
    """判断指定年份是否在有效期范围内"""
    if not date_range:
        return False
    
    start_year, start_month, end_year, end_month = date_range
    return start_year <= year <= end_year


def parse_training_date(date_str):
    """
    解析培训日期，如 '2023/6/22' 或 '2023.6.22'
    返回 (year, month)
    """
    if not date_str:
        return None
    
    try:
        date_str = str(date_str).strip()
        date_parts = date_str.replace('.', '/').split('/')
        
        if len(date_parts) >= 2:
            year = int(date_parts[0])
            month = int(date_parts[1])
            return (year, month)
    except Exception as e:
        print(f"      ❌ 培训日期解析错误: {date_str}")
    
    return None


def check_single_file(file_path):
    """
    检查单个Excel文件 - 根据固定单元格位置
    """
    file_errors = []
    file_name = os.path.basename(file_path)
    
    print(f"\n📄 检查��件: {file_name}")
    
    try:
        wb = load_workbook(file_path)
        ws = wb.active
        
        print(f"   📋 工作表名: {ws.title}")
        print(f"   📊 行数: {ws.max_row}, 列数: {ws.max_column}\n")
        
        # ===== 规则1: 2025年度是否需要参加测评 =====
        print(f"   [规则1] 检查2025年度是否需要参加测评")
        
        # 读取指定单元格
        test_2025_label = get_cell_value(ws, 'E5')
        test_2025_value = get_cell_value(ws, 'H5')
        valid_period_label = get_cell_value(ws, 'F6')
        valid_period_value = get_cell_value(ws, 'H6')
        
        print(f"      E5 标签: {test_2025_label}")
        print(f"      H5 值: {test_2025_value}")
        print(f"      F6 标签: {valid_period_label}")
        print(f"      H6 值: {valid_period_value}")
        
        if test_2025_value and valid_period_value:
            # 解析有效期
            date_range = parse_date_range(valid_period_value)
            if date_range:
                is_in_range = is_year_in_range(2025, date_range)
                expected_value = "否" if is_in_range else "是"
                
                print(f"      有效期: {valid_period_value} -> {date_range}")
                print(f"      2025在范围内: {is_in_range}")
                print(f"      期望值: {expected_value}, 实际值: {test_2025_value}")
                
                if test_2025_value != expected_value:
                    print(f"      ❌ 检查失败")
                    file_errors.append({
                        'file': file_name,
                        'row': '5',
                        'check_type': '规则1',
                        'field': '2025年度是否需要参加测评',
                        'expected': expected_value,
                        'actual': test_2025_value,
                        'message': f"2025年度是否需要参加测评值不对，应为'{expected_value}'，实际为'{test_2025_value}'"
                    })
                else:
                    print(f"      ✅ 检查通过")
            else:
                print(f"      ⚠️ 无法解析有效期")
        else:
            print(f"      ⚠️ 未找到必要的值")
        
        # ===== 规则2: 第三方测评培训时间 =====
        print(f"\n   [规则2] 检查第三方测评培训时间")
        
        training_label = get_cell_value(ws, 'B9')
        training_value = get_cell_value(ws, 'D9')
        
        print(f"      B9 标签: {training_label}")
        print(f"      D9 值: {training_value}")
        
        if training_value and valid_period_value:
            date_range = parse_date_range(valid_period_value)
            if date_range:
                start_year, start_month, end_year, end_month = date_range
                
                # 解析培训时间
                training_date = parse_training_date(training_value)
                if training_date:
                    training_year, training_month = training_date
                    
                    print(f"      有效期开始: {start_year}.{start_month}")
                    print(f"      培训时间: {training_year}.{training_month}")
                    
                    # 检查：培训时间应在有效期开始日期之前且为同一年
                    if training_year == start_year and training_month < start_month:
                        print(f"      ✅ 检查通过")
                    else:
                        print(f"      ❌ 检查失败")
                        file_errors.append({
                            'file': file_name,
                            'row': '9',
                            'check_type': '规则2',
                            'field': '第三方测评培训时间',
                            'expected': f'在{start_year}.{start_month}之前的同一年',
                            'actual': training_value,
                            'message': f"第三方测评培训时间不对，应在有效期开始日期({start_year}.{start_month})之前的同一年，实际为 {training_value}"
                        })
                else:
                    print(f"      ⚠️ 无法解析培训时间")
            else:
                print(f"      ⚠️ 无法解析有效期")
        else:
            print(f"      ⚠️ 未找到培训时间或有效期")
        
        # ===== 规则3: 考试成绩 =====
        print(f"\n   [规则3] 检查考试成绩")
        
        score_label = get_cell_value(ws, 'H19')
        print(f"      H19 标签: {score_label}")
        
        low_scores = []
        
        # H列从19行以下读取成绩数据
        for row_idx in range(20, ws.max_row + 1):
            cell_address = f'H{row_idx}'
            score_value = get_cell_value(ws, cell_address)
            
            if score_value:
                try:
                    score = float(score_value)
                    if score < 90:
                        low_scores.append({
                            'row': row_idx,
                            'score': score,
                            'cell': cell_address
                        })
                        print(f"      行{row_idx} ({cell_address}): 成绩 {score} < 90 ❌")
                except ValueError:
                    # 不是数字，跳过
                    pass
        
        if low_scores:
            for item in low_scores:
                file_errors.append({
                    'file': file_name,
                    'row': str(item['row']),
                    'check_type': '规则3',
                    'field': '考试成绩',
                    'expected': '≥90',
                    'actual': item['score'],
                    'message': f"成绩低于90，实际成绩为 {item['score']}"
                })
            print(f"      发现 {len(low_scores)} 条成绩低于90的记录")
        else:
            print(f"      ✅ 所有成绩均≥90")
    
    except Exception as e:
        print(f"   ❌ 文件处理异常: {e}")
        traceback.print_exc()
        file_errors.append({
            'file': file_name,
            'row': '',
            'check_type': '文件读取',
            'field': '',
            'expected': '',
            'actual': '',
            'message': f"文件读取失败: {str(e)}"
        })
    
    return file_errors


def main():
    """主程序"""
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
        if file.endswith(('.xlsx', '.xls')) and not file.startswith('检查结果'):
            file_path = os.path.join(check_folder, file)
            excel_files.append(file_path)
    
    if not excel_files:
        print(f"⚠️ 文件夹中没有找到Excel文件: {check_folder}")
        return
    
    print(f"✅ 找到 {len(excel_files)} 个Excel文件，开始检查...\n")
    
    # 遍历每个文件进行检查
    all_errors = []
    for file_path in excel_files:
        file_errors = check_single_file(file_path)
        all_errors.extend(file_errors)
        if file_errors:
            print(f"   ⚠️ 发现 {len(file_errors)} 个错误")
        else:
            print(f"   ✅ 检查完成，无错误")
    
    # 输出结果到Excel
    output_file = os.path.join(check_folder, '检查结果.xlsx')
    
    if all_errors:
        result_list = []
        for error in all_errors:
            result_list.append({
                '文件名': error['file'],
                '行号': error['row'],
                '检查项': error['check_type'],
                '字段名': error['field'],
                '期望值': error['expected'],
                '实际值': error['actual'],
                '错误信息': error['message']
            })
        
        result_df = pd.DataFrame(result_list)
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            result_df.to_excel(writer, sheet_name='检查结果', index=False)
            
            # 自动调整列宽
            worksheet = writer.sheets['检查结果']
            col_widths = {
                'A': 20,  # 文件名
                'B': 10,  # 行号
                'C': 10,  # 检查项
                'D': 20,  # 字段名
                'E': 15,  # 期望值
                'F': 15,  # 实际值
                'G': 40   # 错误信息
            }
            for col, width in col_widths.items():
                worksheet.column_dimensions[col].width = width
        
        print(f"\n✅ 检查完成！发现 {len(all_errors)} 个错误")
        print(f"📊 结果已保存到: {output_file}")
    else:
        result_df = pd.DataFrame({
            '文件名': ['检查完成'],
            '行号': [''],
            '检查项': [''],
            '字段名': [''],
            '期望值': [''],
            '实际值': [''],
            '错误信息': ['所有文件均检查通过，无错误']
        })
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            result_df.to_excel(writer, sheet_name='检查结果', index=False)
        
        print(f"\n✅ 检查完成！所有文件均检查通过，无错误")
        print(f"📊 结果已保存到: {output_file}")


if __name__ == '__main__':
    print("=" * 60)
    print("📋 表格检查工具 v3 (精确单元格定位)")
    print("=" * 60)
    
    main()
    
    print("\n✨ 程序执行完毕")
