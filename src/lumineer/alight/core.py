import os
import importlib
import importlib.util
import sys
from types import ModuleType
import shutil

import appdirs

# Application data directory
BASE_DIR = os.path.join(appdirs.user_data_dir(), "Lumineer", "Alight")

class KnowledgeNode:
    def __init__(self, path):
        self._path = path
        self._ensure_directory()
        self._module = self._ensure_module()
        self._children = {}

    def _ensure_directory(self):
        dir_path = os.path.join(BASE_DIR, self._path.replace('.', os.sep))
        os.makedirs(dir_path, exist_ok=True)
        init_file = os.path.join(dir_path, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write("# This is an auto-generated module\n")

    def _ensure_module(self):
        module_name = f"alight.{self._path}" if self._path else "alight"
        try:
            return importlib.import_module(module_name)
        except ImportError:
            spec = importlib.util.spec_from_file_location(
                module_name,
                os.path.join(BASE_DIR, self._path.replace('.', os.sep), 
                             '__init__.py')
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module

    def __getattr__(self, name):
        if name in self._children:
            return self._children[name]
        
        new_path = f"{self._path}.{name}" if self._path else name
        new_node = KnowledgeNode(new_path)
        self._children[name] = new_node
        return new_node

    def __repr__(self):
        return f"KnowledgeNode('{self._path}')"

    def create_node(self, name):
        if '.' in name:
            parts = name.split('.')
            current = self
            for part in parts[:-1]:
                current = getattr(current, part)
            current.create_node(parts[-1])
        else:
            new_path = f"{self._path}.{name}" if self._path else name
            new_node = KnowledgeNode(new_path)
            self._children[name] = new_node
            setattr(self._module, name, new_node)

    def create_leaf(self, name, content=""):
        if '.' in name:
            parts = name.split('.')
            current = self
            for part in parts[:-1]:
                current = getattr(current, part)
            current.create_leaf(parts[-1], content)
        else:
            file_path = os.path.join(BASE_DIR, self._path.replace('.', os.sep), 
                                     f"{name}.py")
            with open(file_path, 'w') as f:
                f.write(f"content = '''{content}'''\n")
            module_name = f"alight.{self._path}.{name}" if self._path else f"alight.{name}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            setattr(self._module, name, module)
            sys.modules[module_name] = module

    def read(self):
        result = {}
        dir_path = os.path.join('src', 'lumineer', 'alight', 
                                self._path.replace('.', os.sep))
        for item in os.listdir(dir_path):
            if item == '__init__.py' or item == 'core.py' or item == 'gui.py' or item.startswith('__'):
                continue
            if item.endswith('.py'):
                name = item[:-3]
                module_path = f"lumineer.alight.{self._path}.{name}"
                module = importlib.import_module(module_path)
                result[name] = getattr(module, 'content', '')
            elif os.path.isdir(os.path.join(dir_path, item)):
                result[item] = f"KnowledgeNode('{self._path}.{item}')"
        return result

    def update_node(self, name):
        # Nodes (packages) don't have content to update
        pass

    def update_leaf(self, name, content):
        if '.' in name:
            parts = name.split('.')
            current = self
            for part in parts[:-1]:
                current = getattr(current, part)
            current.update_leaf(parts[-1], content)
        else:
            file_path = os.path.join('src', 'lumineer', 'alight', 
                                     self._path.replace('.', os.sep), 
                                     f"{name}.py")
            with open(file_path, 'w') as f:
                f.write(f"content = '''{content}'''\n")
            module_name = f"lumineer.alight.{self._path}.{name}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            setattr(self._module, name, module)
            sys.modules[module_name] = module

    def delete(self, name):
        if '.' in name:
            parts = name.split('.')
            current = self
            for part in parts[:-1]:
                current = getattr(current, part)
            current.delete(parts[-1])
        else:
            path = os.path.join('src', 'lumineer', 'alight', 
                                self._path.replace('.', os.sep))
            file_path = os.path.join(path, f"{name}.py")
            dir_path = os.path.join(path, name)
            
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(dir_path):
                shutil.rmtree(dir_path)
            
            if hasattr(self._module, name):
                delattr(self._module, name)
            if name in self._children:
                del self._children[name]
            module_name = f"lumineer.alight.{self._path}.{name}"
            if module_name in sys.modules:
                del sys.modules[module_name]

def create_alight():
    return KnowledgeNode("")

alight = create_alight()