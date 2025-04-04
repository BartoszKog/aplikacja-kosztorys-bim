from flet import (
    Row,
    Container
)

class Body(Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        
        self.left_content = Container(expand=True)
        self.right_content = Container(expand=True)
        
        self.main_row = Row(expand=True)
        self.content = self.main_row
        
    def add_content(self, content, side='left'):
        if side == 'left':
            self.left_content.content = content
        elif side == 'right':
            self.right_content.content = content
        
        self.main_row.controls.clear()
        
        if self.left_content.content:
            self.main_row.controls.insert(0, self.left_content)
        if self.right_content.content:
            self.main_row.controls.append(self.right_content)
        
        self.update()
        
    def delete_content(self, side: str):
        if side not in ['left', 'right']:
            raise ValueError('side must be either "left" or "right"')
        
        content_container = self.left_content if side == 'left' else self.right_content
        content_container.content = None
            
        self.main_row.controls = [
            container for container in [self.left_content, self.right_content] if container.content
        ]
        
        self.update()
        
    def get_control(self, side: str):
        if side not in ['left', 'right']:
            raise ValueError('side must be either "left" or "right"')
        
        if side == 'left':
            if self.left_content.content:
                return self.left_content.content
            
        elif side == 'right':
            if self.right_content.content:
                return self.right_content.content
    
    def has_content(self, control, side: str) -> bool:
        if side not in ['left', 'right']:
            raise ValueError('side must be either "left" or "right"')
        
        content_container = self.left_content if side == 'left' else self.right_content
        return content_container.content == control


