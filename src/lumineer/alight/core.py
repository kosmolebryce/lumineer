import os
import importlib
import importlib.util
import sys
from types import ModuleType
import shutil

import appdirs

BASE_DIR = os.path.join(appdirs.user_data_dir(), "Lumineer", "Alight")

class AlightFinder:
    @classmethod
    def find_spec(cls, fullname, path, target=None):
        if fullname.startswith("alight"):
            parts = fullname.split('.')
            mod_path = os.path.join(BASE_DIR, *parts[1:])
            if os.path.isdir(mod_path):
                filename = os.path.join(mod_path, "__init__.py")
            else:
                filename = mod_path + ".py"
            if os.path.exists(filename):
                return importlib.util.spec_from_file_location(fullname, filename)
        return None

sys.meta_path.insert(0, AlightFinder)

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
        return importlib.import_module(module_name)

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
            print(f"Created node: {new_path}")

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
            importlib.invalidate_caches()
            module = importlib.import_module(module_name)
            setattr(self._module, name, module)

    def read(self):
        result = {}
        dir_path = os.path.join(BASE_DIR, self._path.replace('.', os.sep))
        if not os.path.exists(dir_path):
            return result
        for item in os.listdir(dir_path):
            if item == '__init__.py' or item.startswith('__'):
                continue
            if item.endswith('.py'):
                name = item[:-3]
                module_path = f"alight.{self._path}.{name}" if self._path else f"alight.{name}"
                try:
                    module = importlib.import_module(module_path)
                    result[name] = getattr(module, 'content', '')
                except ImportError:
                    print(f"Failed to import {module_path}")
            elif os.path.isdir(os.path.join(dir_path, item)):
                result[item] = f"KnowledgeNode('{self._path}.{item}' if self._path else '{item}')"
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
            path = os.path.join(BASE_DIR, self._path.replace('.', os.sep))
            file_path = os.path.join(path, f"{name}.py")
            dir_path = os.path.join(path, name)
            
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            elif os.path.isdir(dir_path):
                shutil.rmtree(dir_path)
                print(f"Deleted directory: {dir_path}")
            
            if hasattr(self._module, name):
                delattr(self._module, name)
            if name in self._children:
                del self._children[name]
            module_name = f"alight.{self._path}.{name}" if self._path else f"alight.{name}"
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            print(f"Deleted node/leaf: {name} from {self._path}")

def create_alight():
    return KnowledgeNode("")

alight = create_alight()