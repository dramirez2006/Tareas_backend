import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app import models, financial_models, rbac_models  # noqa: F401
from app.rbac import seed_rbac
from app.rbac_models import PermissionModel, RoleModel, RolePermissionModel


class SeedRbacTest(unittest.TestCase):
    def test_restart_preserves_fully_disabled_role(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            seed_rbac(db)
            role = db.scalar(select(RoleModel).where(RoleModel.code == "CAPTURISTA"))
            entries = db.scalars(select(RolePermissionModel).where(RolePermissionModel.role_id == role.id)).all()
            self.assertEqual(len(entries), 4)
            for entry in entries:
                entry.is_active = False
            db.commit()
            seed_rbac(db)
            self.assertEqual(len(db.scalars(select(RolePermissionModel).where(RolePermissionModel.role_id == role.id)).all()), 4)
            self.assertEqual(len(db.scalars(select(RolePermissionModel).where(RolePermissionModel.role_id == role.id, RolePermissionModel.is_active.is_(True))).all()), 0)
            self.assertEqual(len(db.scalars(select(RoleModel)).all()), 4)
            self.assertEqual(len(db.scalars(select(PermissionModel)).all()), 10)


if __name__ == "__main__":
    unittest.main()
