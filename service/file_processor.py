import io
import pandas as pd
from typing import List, Dict, Any
from fastapi import UploadFile, HTTPException


class FileProcessor:
    
    @staticmethod
    async def process_csv_excel(file: UploadFile) -> List[Dict[str, Any]]:
        """Process CSV or Excel file and return list of dictionaries"""
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        content = await file.read()
        
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(io.StringIO(content.decode('utf-8')))
            elif file.filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(io.BytesIO(content))
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV or Excel files.")
            
            # Convert DataFrame to list of dictionaries
            return df.to_dict('records')
        
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")
    
    @staticmethod
    def validate_grades_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate grades data structure"""
        required_fields = ['label', 'value']
        validated_data = []
        
        for row in data:
            if not all(field in row for field in required_fields):
                raise HTTPException(status_code=400, detail=f"Missing required fields: {required_fields}")
            
            try:
                validated_data.append({
                    'label': str(row['label']),
                    'value': int(row['value'])
                })
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="Invalid data types in grades file")
        
        return validated_data
    
    @staticmethod
    def validate_skills_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate skills data structure"""
        required_fields = ['name']
        validated_data = []
        
        for row in data:
            if 'name' not in row:
                raise HTTPException(status_code=400, detail="Missing required field: name")
            
            validated_row = {
                'name': str(row['name']),
                'description': str(row.get('description', '')) if row.get('description') else None,
                'deleted': bool(row.get('deleted', False)),
                'parent_id': int(row['parent_id']) if row.get('parent_id') and pd.notna(row['parent_id']) else None
            }
            validated_data.append(validated_row)
        
        return validated_data
    
    @staticmethod
    def validate_user_skills_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate user skills data structure"""
        required_fields = ['user_id', 'skill_id', 'grade_id']
        validated_data = []
        
        for row in data:
            if not all(field in row for field in required_fields):
                raise HTTPException(status_code=400, detail=f"Missing required fields: {required_fields}")
            
            try:
                validated_row = {
                    'user_id': int(row['user_id']),
                    'skill_id': int(row['skill_id']),
                    'grade_id': int(row['grade_id']),
                    'note': str(row.get('note', '')) if row.get('note') else None
                }
                validated_data.append(validated_row)
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="Invalid data types in user skills file")
        
        return validated_data