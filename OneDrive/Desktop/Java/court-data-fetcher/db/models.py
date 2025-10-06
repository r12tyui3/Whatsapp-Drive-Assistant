from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()

class QueryLog(Base):
    __tablename__ = "query_logs"
    id = Column(String, primary_key=True)
    portal = Column(String, nullable=False)  # HIGH_COURT or DISTRICT_COURT
    court = Column(Text)  # JSON-ish text; HC name or state/district
    case_type = Column(String, nullable=False)
    case_number = Column(String, nullable=False)
    case_year = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    status = Column(String, default="OK")

    raw_response = relationship("RawResponse", back_populates="query", uselist=False)
    case_detail = relationship("CaseDetail", back_populates="query", uselist=False)
    orders = relationship("OrderDocument", back_populates="query")

class RawResponse(Base):
    __tablename__ = "raw_responses"
    id = Column(String, primary_key=True)
    query_id = Column(String, ForeignKey("query_logs.id"))
    html = Column(Text, nullable=False)

    query = relationship("QueryLog", back_populates="raw_response")

class CaseDetail(Base):
    __tablename__ = "case_details"
    id = Column(String, primary_key=True)
    query_id = Column(String, ForeignKey("query_logs.id"))
    parties = Column(Text)
    filing_date = Column(String)
    next_hearing_date = Column(String)
    case_status = Column(String)

    query = relationship("QueryLog", back_populates="case_detail")

class OrderDocument(Base):
    __tablename__ = "order_documents"
    id = Column(String, primary_key=True)
    query_id = Column(String, ForeignKey("query_logs.id"))
    title = Column(Text)
    order_date = Column(String)
    file_path = Column(Text)       # local saved path if downloaded
    source_url = Column(Text)      # original link (fallback)

    query = relationship("QueryLog", back_populates="orders")
