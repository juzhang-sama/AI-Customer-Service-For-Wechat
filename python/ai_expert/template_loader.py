# -*- coding: utf-8 -*-
"""
Template Loader
行业模板加载器
"""

import json
import os
from typing import List, Dict, Optional

class TemplateLoader:
    def __init__(self):
        self.templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    
    def get_all_templates(self) -> List[Dict]:
        """获取所有模板"""
        templates = []
        
        if not os.path.exists(self.templates_dir):
            return templates
        
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.json'):
                template = self.load_template(filename[:-5])
                if template:
                    templates.append(template)
        
        return templates
    
    def load_template(self, template_name: str) -> Optional[Dict]:
        """
        加载指定模板
        
        Args:
            template_name: 模板名称（不含.json后缀）
        
        Returns:
            模板数据字典
        """
        template_path = os.path.join(self.templates_dir, f"{template_name}.json")
        
        if not os.path.exists(template_path):
            return None
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = json.load(f)
                template['template_id'] = template_name
                return template
        except Exception as e:
            print(f"Error loading template {template_name}: {e}")
            return None
    
    def get_template_list(self) -> List[Dict]:
        """获取模板列表（仅基本信息）"""
        templates = self.get_all_templates()
        
        return [
            {
                'id': t.get('template_id'),
                'name': t.get('name'),
                'description': t.get('description')
            }
            for t in templates
        ]

