from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime


from config.database.session import Base


class ProductFundORM(Base):
    __tablename__ = "product_fund"
    id = Column(Integer, primary_key=True, index=True)
    basDt = Column(DateTime, default=datetime.utcnow)       # 기준일자
    srtnCd = Column(String(255), nullable=True)             # 단축코드
    fndNm = Column(String(255), nullable=True)              # 펀드명
    ctg = Column(String(255), nullable=True)                # 구분
    setpDt = Column(DateTime, nullable=True)                # 설정일
    fndTp = Column(String(255), nullable=True)              # 펀드유형
    prdClsfCd = Column(String(255), nullable=True)          # 상품분류코드
    asoStdCd = Column(String(255), nullable=True)           # 협회표준코드

    def __repr__(self):
        return f"<ProductFundORM id={self.id}>"