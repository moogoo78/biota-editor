from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# auth
class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: Optional[str] = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORM):
    id: int
    email: str
    name: Optional[str]


class TokenOut(BaseModel):
    token: str
    user: UserOut


class NotificationOut(ORM):
    id: int
    content: str
    publication_id: Optional[int]
    created_at: datetime
    read_at: Optional[datetime]


# publications
class LiteratureOut(ORM):
    id: int
    reference_id: Optional[int]
    citation: str
    sort: int


class LiteratureIn(BaseModel):
    reference_id: Optional[int] = None
    citation: str


class SynonymOut(ORM):
    id: int
    name_id: Optional[int]
    usage_text: str


class SpecimenOut(ORM):
    id: int
    source: str
    occurrence_id: str
    scientific_name: Optional[str]
    catalog_number: Optional[str]
    recorded_by: Optional[str]
    record_number: Optional[str]
    locality: Optional[str]
    county: Optional[str]
    institution_code: Optional[str]
    dataset_name: Optional[str]
    event_date: Optional[str]
    type_status: Optional[str]
    display_text: str
    sort: int
    link: Optional[str] = None


class ImageOut(ORM):
    id: int
    source: str
    source_id: str
    url: str
    thumb_url: Optional[str]
    link: Optional[str]
    attribution: Optional[str]
    license: Optional[str]
    caption: Optional[str]
    sort: int


class ItemSummary(ORM):
    id: int
    name_id: Optional[int]
    rank_id: Optional[int]
    rank: Optional[list[str]] = None
    scientific_name: str
    name_html: Optional[str]
    name_authors: Optional[str]
    common_names: Optional[str]
    sort: int
    n_specimens: int = 0
    n_images: int = 0
    n_synonyms: int = 0


class ItemOut(ItemSummary):
    usage_text: Optional[str]
    description: Optional[str]
    distribution: Optional[str]
    note: Optional[str]
    edited_fields: list[str] = []
    synonyms: list[SynonymOut] = []
    specimens: list[SpecimenOut] = []
    images: list[ImageOut] = []
    search_names: list[str] = []


class ItemPatch(BaseModel):
    common_names: Optional[str] = None
    description: Optional[str] = None
    distribution: Optional[str] = None
    note: Optional[str] = None


class RevertIn(BaseModel):
    fields: list[str]


class PublicationSummary(ORM):
    id: int
    namespace_id: int
    title: str
    author: str
    status: str
    synced_at: Optional[datetime]
    updated_at: datetime
    n_items: int = 0


class PublicationOut(PublicationSummary):
    literatures: list[LiteratureOut] = []
    items: list[ItemSummary] = []


class PublicationPatch(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    status: Optional[str] = None


class ImportIn(BaseModel):
    namespace_id: int


class ImportOut(BaseModel):
    publication_id: int
    status: str
    counts: dict[str, int]


class OrderIn(BaseModel):
    ids: list[int]


# specimens / images
class SpecimenPick(BaseModel):
    occurrence_id: str
    display_text: Optional[str] = None
    record: dict[str, Any] = {}


class ImagePick(BaseModel):
    source: str
    source_id: str
    url: str
    thumb_url: Optional[str] = None
    link: Optional[str] = None
    attribution: Optional[str] = None
    license: Optional[str] = None
    caption: Optional[str] = None
    record: dict[str, Any] = {}

    @field_validator("source")
    @classmethod
    def _src(cls, v: str) -> str:
        if v not in ("inat", "taieol"):
            raise ValueError("source must be inat or taieol")
        return v

    @field_validator("url", "thumb_url", "link")
    @classmethod
    def _http(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("must be an http(s) URL")
        return v


# keys
class KeyEntryIn(BaseModel):
    number: int
    indent_level: int = 0
    description: str
    result_couplet: Optional[int] = None
    result_item_id: Optional[int] = None


class KeyEntryOut(KeyEntryIn, ORM):
    id: int


class KeyIn(BaseModel):
    title: Optional[str] = None
    entries: list[KeyEntryIn] = []


class KeyOut(ORM):
    id: int
    title: Optional[str]
    entries: list[KeyEntryOut] = []
