"""
尺码表格式化工具
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple


class SizeTableFormatter:
    """将日文尺码信息转换为中文纯文本表格"""

    SIZE_MAP = {
        'XS': 'XS码',
        'S': 'S码',
        'M': 'M码',
        'L': 'L码',
        'LL': 'XL码',
        'XL': 'XL码',
        '3L': '2XL码',
        'XXL': '2XL码',
        '4L': '3XL码',
        'XXXL': '3XL码',
        '5L': '4XL码',
        'フリー': '均码',
        'FREE': '均码'
    }

    MEASURE_MAP = [
        ('バスト', '胸围'),
        ('身幅', '衣宽'),
        ('身丈', '衣长'),
        ('着丈', '衣长'),
        ('裄丈', '袖长(从后领中心到袖口)'),
        ('袖丈', '袖长(从肩点到袖口)'),
        ('肩幅', '肩宽'),
        ('袖口幅', '袖口宽'),
        ('裾幅', '下摆宽'),
        ('前下がり', '前片长度'),
        ('後ろ下がり', '后片长度'),
        ('ウエスト', '腰围'),
        ('最小ウエスト', '最小腰围'),
        ('最大ウエスト', '最大腰围'),
        ('ヒップ', '臀围'),
        ('股下', '裤长'),
        ('股上', '裆长'),
        ('わたり幅', '大腿围'),
        ('総丈', '全长'),
        ('全長', '全长'),
        ('ベルト巾', '腰带宽度'),
        ('バックル巾', '扣头宽度'),
        ('持ち手の高さ(cm)', '提手高度(cm)'),
        ('重さ', '重量'),
        ('原産国', '原产国'),
        ('クロージング', '闭合方式'),
        ('シーズン', '季节')
    ]

    NOTE_KEYWORDS = [
        ('仕上がり', '以上为成品尺寸'),
        ('実寸', '以上为成品尺寸'),
        ('1-2cm', '因面料特性，实际尺寸可能存在1-2cm误差'),
        ('１-２cm', '因面料特性，实际尺寸可能存在1-2cm误差'),
        ('ヌード寸法', '商品标签为净体尺寸，请结合尺码表选择'),
        ('ゆとり', '版型含适度放松量'),
    ]

    DEFAULT_NOTES = [
        '以上为成品尺寸',
        '因面料特性，实际尺寸可能存在1-2cm误差'
    ]

    def build(self, size_text: Optional[str], structured_chart: Optional[Dict]) -> str:
        lines: List[str] = []
        notes: List[str] = []

        text_lines, text_notes = self._format_from_text(size_text or '')
        lines.extend(text_lines)
        notes.extend(text_notes)

        if not lines and structured_chart:
            chart_lines, chart_notes = self._format_from_structured(structured_chart)
            lines.extend(chart_lines)
            notes.extend(chart_notes)

        if not lines:
            return ''

        note_block = self._build_note_block(notes)
        return '\n'.join(lines) + note_block

    # ------------------------------------------------------------------ #
    # 内部实现
    # ------------------------------------------------------------------ #

    def _format_from_text(self, text: str) -> Tuple[List[str], List[str]]:
        if not text:
            return [], []

        lines: List[str] = []
        notes: List[str] = []

        normalized_text = text.replace('／', '/').replace('～', '~')
        for raw_line in normalized_text.splitlines():
            line = raw_line.strip(' 　')
            if not line:
                continue

            if line.startswith('※') or any(keyword in line for keyword, _ in self.NOTE_KEYWORDS):
                translated_note = self._translate_note(line)
                if translated_note:
                    notes.append(translated_note)
                continue

            if '/' not in line:
                # 过滤标题，例如"商品サイズ"
                continue

            segments = [seg.strip() for seg in line.split('/') if seg.strip()]
            if len(segments) < 2:
                continue

            size_label = self._map_size_label(segments[0])
            if not size_label:
                continue

            measurement_parts: List[str] = []
            for segment in segments[1:]:
                name, value = self._translate_measurement(segment)
                if name and value:
                    measurement_parts.append(f"{name}{value}")

            if measurement_parts:
                lines.append(f"【{size_label}】" + " | ".join(measurement_parts))

        return lines, notes

    def _format_from_html_text(self, html_or_text: str) -> Tuple[List[str], List[str]]:
        """从HTML或文本格式解析尺码表信息"""
        if not html_or_text:
            return [], []

        lines = []
        notes = []

        # 如果包含HTML标签，尝试解析HTML表格
        if '<table' in html_or_text:
            try:
                import re

                # 提取表格内容
                table_content = self._extract_table_from_html(html_or_text)
                if table_content:
                    lines.extend(table_content)
                    return lines, []
            except Exception as e:
                # HTML解析失败，回退到文本解析
                pass

        # 从文本中提取键值对信息
        lines, notes = self._format_from_text(html_or_text)
        return lines, notes

    def _extract_table_from_html(self, html: str) -> List[str]:
        """从HTML表格中提取尺码表信息"""
        import re

        # 提取表格中的行
        tr_pattern = r'<tr[^>]*>(.*?)</tr>'
        rows = re.findall(tr_pattern, html, re.DOTALL)

        extracted_lines = []
        key_value_pairs = {}  # 用于存储key-value对

        for row in rows:
            # 同时提取表头(th)和单元格(td)
            th_pattern = r'<th[^>]*>(.*?)</th>'
            td_pattern = r'<td[^>]*>(.*?)</td>'

            headers = re.findall(th_pattern, row, re.DOTALL)
            cells = re.findall(td_pattern, row, re.DOTALL)

            # 清理HTML标签并提取文本
            clean_headers = []
            for header in headers:
                clean_text = re.sub(r'<[^>]+>', '', header).strip()
                clean_text = re.sub(r'\s+', ' ', clean_text)  # 合并多个空格
                if clean_text:
                    clean_headers.append(clean_text)

            clean_cells = []
            for cell in cells:
                # 移除HTML标签
                clean_text = re.sub(r'<[^>]+>', '', cell).strip()
                clean_text = re.sub(r'\s+', ' ', clean_text)  # 合并多个空格
                if clean_text:
                    clean_cells.append(clean_text)

            # 处理表头-单元格配对
            if clean_headers and clean_cells:
                for header, cell in zip(clean_headers, clean_cells):
                    if header and cell:
                        # 跳过纯商品编号和品牌信息
                        if any(keyword in header for keyword in ['商品番号', 'ブランド商品番号', 'ブランド名']):
                            continue

                        # 翻译键名
                        translated_key = self._translate_measurement_name(header)
                        if translated_key and translated_key != header:
                            key_value_pairs[translated_key] = cell
                        else:
                            key_value_pairs[header] = cell

            # 处理只有单元格的情况（单列数据）
            elif len(clean_cells) == 1:
                # 这种情况可能是简单的值，尝试与之前的表头配对
                pass  # 暂时跳过，因为我们没有上下文

        # 生成输出行
        for key, value in key_value_pairs.items():
            extracted_lines.append(f"{key}: {value}")

        return extracted_lines

    def _format_from_structured(self, chart: Dict) -> Tuple[List[str], List[str]]:
        # 优先处理新的 text/html 格式（我们的JSON格式）
        # 优先使用html字段，因为它包含完整的表格结构
        html_content = chart.get('html', '') or chart.get('text', '')
        if html_content:
            return self._format_from_html_text(html_content)

        # 兼容旧的 headers/rows 格式
        headers = chart.get('headers') or []
        rows = chart.get('rows') or []
        if not headers or not rows:
            return [], []

        size_header = headers[0]
        measure_headers = headers[1:]
        translated_headers = [self._translate_measurement_name(h) for h in measure_headers]

        lines: List[str] = []
        for row in rows:
            if not row:
                continue
            size_value = row[0]
            size_label = self._map_size_label(str(size_value))
            if not size_label:
                continue

            measurements = []
            for idx, value in enumerate(row[1:]):
                if idx >= len(translated_headers):
                    break
                header_name = translated_headers[idx]
                value_str = str(value).strip()
                if header_name and value_str:
                    measurements.append(f"{header_name}{value_str}")

            if measurements:
                lines.append(f"【{size_label}】" + " | ".join(measurements))

        return lines, []

    def _map_size_label(self, token: str) -> str:
        if not token:
            return ''
        normalized = token.upper()
        normalized = re.sub(r'サイズ', '', normalized)
        normalized = normalized.strip()
        if normalized in self.SIZE_MAP:
            return self.SIZE_MAP[normalized]
        if normalized.endswith('L') and normalized[:-1].isdigit():
            # 2L,3L结构
            mapping = {
                '2L': 'XL码',
                '3L': '2XL码',
                '4L': '3XL码',
                '5L': '4XL码'
            }
            return mapping.get(normalized, f"{normalized}码")
        if normalized:
            return f"{normalized}码"
        return ''

    def _translate_measurement(self, segment: str) -> Tuple[str, str]:
        cleaned = segment.replace('：', ' ').replace(':', ' ')
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        if not cleaned:
            return '', ''

        match = re.match(r'([^\d]+)\s*(.+)', cleaned)
        if not match:
            return '', ''

        label = match.group(1).strip()
        value = match.group(2).strip()

        translated_label = self._translate_measurement_name(label)
        return translated_label, value

    def _translate_measurement_name(self, label: str) -> str:
        for jp, cn in self.MEASURE_MAP:
            if label.startswith(jp):
                return cn
        return label

    def _translate_note(self, line: str) -> Optional[str]:
        normalized = line.lstrip('※').strip()
        for keyword, note in self.NOTE_KEYWORDS:
            if keyword in normalized:
                return note
        return None

    def _build_note_block(self, extra_notes: List[str]) -> str:
        notes = []
        seen = set()
        for note in self.DEFAULT_NOTES + extra_notes:
            if note and note not in seen:
                seen.add(note)
                notes.append(note)

        if not notes:
            return ''

        note_lines = '\n'.join(f"- {note}" for note in notes)
        return f"\n\n尺码说明:\n{note_lines}"
