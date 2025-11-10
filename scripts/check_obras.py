import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from modules.obras import ObrasManager

m = ObrasManager()

df_all = m.get_obras()
df_active = m.get_obras({'status': 'Ativo'})
print(f"Total obras (sem filtro): {len(df_all)}")
print(f"Total obras (status=Ativo): {len(df_active)}")
if not df_active.empty:
    print(df_active[['id','codigo','nome','status']].head(20))
else:
    print('Nenhuma obra ativa encontrada')
