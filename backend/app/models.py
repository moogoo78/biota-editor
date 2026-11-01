"""BiotaEditor schema (SQLite). Slimmed from biota/app/models.py: biota's
Publication + Collection (always 1:1) are merged into Publication."""
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)


class User(Base, TimestampMixin):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(default=True)

    publications: Mapped[list["Publication"]] = relationship(back_populates="user")
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", order_by="Notification.id.desc()"
    )


class WebhookEvent(Base, TimestampMixin):
    __tablename__ = "webhook_event"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
    result: Mapped[Optional[str]] = mapped_column(String(500))


class Notification(Base, TimestampMixin):
    __tablename__ = "notification"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text)
    event_id: Mapped[Optional[int]] = mapped_column(ForeignKey("webhook_event.id"))
    publication_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("publication.id", ondelete="SET NULL")
    )
    read_at: Mapped[Optional[datetime]] = mapped_column()

    user: Mapped[User] = relationship(back_populates="notifications")


class Publication(Base, TimestampMixin):
    __tablename__ = "publication"
    __table_args__ = (UniqueConstraint("user_id", "namespace_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    namespace_id: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(500), default="")
    author: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(String(50), default="draft")
    source_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    synced_at: Mapped[Optional[datetime]] = mapped_column()

    user: Mapped[User] = relationship(back_populates="publications")
    literatures: Mapped[list["PublicationLiterature"]] = relationship(
        back_populates="publication", order_by="PublicationLiterature.sort",
        cascade="all, delete-orphan",
    )
    items: Mapped[list["Item"]] = relationship(
        back_populates="publication", order_by="Item.sort", cascade="all, delete-orphan"
    )
    keys: Mapped[list["IdentificationKey"]] = relationship(
        back_populates="publication", cascade="all, delete-orphan"
    )


class PublicationLiterature(Base):
    __tablename__ = "publication_literature"

    id: Mapped[int] = mapped_column(primary_key=True)
    publication_id: Mapped[int] = mapped_column(
        ForeignKey("publication.id", ondelete="CASCADE"), index=True
    )
    reference_id: Mapped[Optional[int]] = mapped_column(Integer)
    citation: Mapped[str] = mapped_column(Text)
    sort: Mapped[int] = mapped_column(Integer, default=0)

    publication: Mapped[Publication] = relationship(back_populates="literatures")


class Item(Base, TimestampMixin):
    """One name of a TaiCOL namespace (a taxon treatment)."""
    __tablename__ = "item"

    id: Mapped[int] = mapped_column(primary_key=True)
    publication_id: Mapped[int] = mapped_column(
        ForeignKey("publication.id", ondelete="CASCADE"), index=True
    )
    name_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    rank_id: Mapped[Optional[int]] = mapped_column(Integer)
    scientific_name: Mapped[str] = mapped_column(String(500))
    name_html: Mapped[Optional[str]] = mapped_column(String(1000))  # "<i>Berberis</i>"
    name_authors: Mapped[Optional[str]] = mapped_column(String(500))
    usage_text: Mapped[Optional[str]] = mapped_column(Text)  # usage_references_text
    common_names: Mapped[Optional[str]] = mapped_column(String(500))  # '|'-joined
    description: Mapped[Optional[str]] = mapped_column(Text)
    distribution: Mapped[Optional[str]] = mapped_column(Text)
    note: Mapped[Optional[str]] = mapped_column(Text)
    sort: Mapped[int] = mapped_column(Integer, default=0)
    source_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    # fields the author edited locally; a TaiCOL sync leaves them alone
    edited_fields: Mapped[list[str]] = mapped_column(JSON, default=list)

    publication: Mapped[Publication] = relationship(back_populates="items")
    synonyms: Mapped[list["ItemSynonym"]] = relationship(
        back_populates="item", order_by="ItemSynonym.sort", cascade="all, delete-orphan"
    )
    specimens: Mapped[list["ItemSpecimen"]] = relationship(
        back_populates="item", order_by="ItemSpecimen.sort", cascade="all, delete-orphan"
    )
    images: Mapped[list["ItemImage"]] = relationship(
        back_populates="item", order_by="ItemImage.sort", cascade="all, delete-orphan"
    )


class ItemSynonym(Base):
    __tablename__ = "item_synonym"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id", ondelete="CASCADE"), index=True)
    name_id: Mapped[Optional[int]] = mapped_column(Integer)
    usage_text: Mapped[str] = mapped_column(Text)
    sort: Mapped[int] = mapped_column(Integer, default=0)

    item: Mapped[Item] = relationship(back_populates="synonyms")


class ItemSpecimen(Base):
    __tablename__ = "item_specimen"
    __table_args__ = (UniqueConstraint("item_id", "source", "occurrence_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(50), default="tbia")
    occurrence_id: Mapped[str] = mapped_column(String(200))
    scientific_name: Mapped[Optional[str]] = mapped_column(String(500))
    catalog_number: Mapped[Optional[str]] = mapped_column(String(200))
    recorded_by: Mapped[Optional[str]] = mapped_column(String(500))
    record_number: Mapped[Optional[str]] = mapped_column(String(200))
    locality: Mapped[Optional[str]] = mapped_column(Text)
    county: Mapped[Optional[str]] = mapped_column(String(100))
    institution_code: Mapped[Optional[str]] = mapped_column(String(100))
    dataset_name: Mapped[Optional[str]] = mapped_column(String(500))
    event_date: Mapped[Optional[str]] = mapped_column(String(50))
    type_status: Mapped[Optional[str]] = mapped_column(String(100))
    display_text: Mapped[str] = mapped_column(Text, default="")
    source_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    sort: Mapped[int] = mapped_column(Integer, default=0)

    item: Mapped[Item] = relationship(back_populates="specimens")


class ItemImage(Base):
    __tablename__ = "item_image"
    __table_args__ = (UniqueConstraint("item_id", "source", "source_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(50))  # inat | taieol
    source_id: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(2000))
    thumb_url: Mapped[Optional[str]] = mapped_column(String(2000))
    link: Mapped[Optional[str]] = mapped_column(String(2000))
    attribution: Mapped[Optional[str]] = mapped_column(Text)
    license: Mapped[Optional[str]] = mapped_column(String(200))
    caption: Mapped[Optional[str]] = mapped_column(Text)
    source_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    sort: Mapped[int] = mapped_column(Integer, default=0)

    item: Mapped[Item] = relationship(back_populates="images")


class IdentificationKey(Base, TimestampMixin):
    __tablename__ = "identification_key"

    id: Mapped[int] = mapped_column(primary_key=True)
    publication_id: Mapped[int] = mapped_column(
        ForeignKey("publication.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(500))

    publication: Mapped[Publication] = relationship(back_populates="keys")
    entries: Mapped[list["KeyEntry"]] = relationship(
        back_populates="key", order_by="KeyEntry.sort", cascade="all, delete-orphan"
    )


class KeyEntry(Base):
    __tablename__ = "key_entry"

    id: Mapped[int] = mapped_column(primary_key=True)
    key_id: Mapped[int] = mapped_column(
        ForeignKey("identification_key.id", ondelete="CASCADE"), index=True
    )
    number: Mapped[int] = mapped_column(Integer)
    indent_level: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text)
    result_couplet: Mapped[Optional[int]] = mapped_column(Integer)
    result_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("item.id", ondelete="SET NULL"))
    sort: Mapped[int] = mapped_column(Integer, default=0)

    key: Mapped[IdentificationKey] = relationship(back_populates="entries")
    result_item: Mapped[Optional[Item]] = relationship()
