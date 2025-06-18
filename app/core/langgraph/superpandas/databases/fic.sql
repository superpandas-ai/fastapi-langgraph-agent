-- Schema for Financial & Invoicing Database

-- PAYMENT ACCOUNTS
CREATE TABLE payment_accounts (
    id INTEGER PRIMARY KEY,
    original_id INTEGER,
    name VARCHAR(255),
    type VARCHAR(8),
    iban VARCHAR(50),
    sia VARCHAR(20),
    cuc VARCHAR(20),
    virtual BOOLEAN
);

-- VAT TYPES
CREATE TABLE vat_types (
    id INTEGER PRIMARY KEY,
    original_id INTEGER,
    value FLOAT,
    description VARCHAR(255),
    notes VARCHAR(255),
    e_invoice BOOLEAN,
    ei_type VARCHAR(10),
    ei_description VARCHAR(255),
    editable BOOLEAN,
    is_disabled BOOLEAN,
    default BOOLEAN
);

-- CURRENCIES
CREATE TABLE currencies (
    id VARCHAR(3) PRIMARY KEY,
    exchange_rate VARCHAR(20),
    symbol VARCHAR(10)
);

-- LANGUAGES
CREATE TABLE languages (
    code VARCHAR(2) PRIMARY KEY,
    name VARCHAR(50)
);

-- PAYMENT METHODS
CREATE TABLE payment_methods (
    id INTEGER PRIMARY KEY,
    original_id INTEGER,
    name VARCHAR(255),
    type VARCHAR(17),
    is_default BOOLEAN,
    default_payment_account_id INTEGER,
    bank_iban VARCHAR(50),
    bank_name VARCHAR(255),
    bank_beneficiary VARCHAR(255),
    ei_payment_method VARCHAR(20),
    FOREIGN KEY(default_payment_account_id) REFERENCES payment_accounts(id)
);

-- PRODUCTS
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    original_id INTEGER,
    code VARCHAR(50),
    name VARCHAR(255),
    description TEXT,
    net_price FLOAT,
    gross_price FLOAT,
    use_gross_price BOOLEAN,
    default_vat_id INTEGER,
    category VARCHAR(255),
    measure VARCHAR(50),
    created_at DATE,
    updated_at DATE,
    FOREIGN KEY(default_vat_id) REFERENCES vat_types(id)
);

-- F24 FORMS
CREATE TABLE f24s (
    id INTEGER PRIMARY KEY,
    original_id INTEGER,
    due_date DATE,
    status VARCHAR(20),
    payment_account_id INTEGER,
    amount FLOAT,
    description TEXT,
    FOREIGN KEY(payment_account_id) REFERENCES payment_accounts(id)
);

-- ENTITIES (CUSTOMERS/SUPPLIERS)
CREATE TABLE entities (
    id INTEGER PRIMARY KEY,
    original_id INTEGER,
    code VARCHAR(50),
    name VARCHAR(255),
    type VARCHAR(7),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    contact_person VARCHAR(255),
    vat_number VARCHAR(50),
    tax_code VARCHAR(50),
    address_street VARCHAR(255),
    address_postal_code VARCHAR(20),
    address_city VARCHAR(255),
    address_province VARCHAR(50),
    address_extra VARCHAR(255),
    country VARCHAR(50),
    country_iso VARCHAR(2),
    email VARCHAR(255),
    certified_email VARCHAR(255),
    phone VARCHAR(50),
    fax VARCHAR(50),
    notes TEXT,
    default_vat_id INTEGER,
    default_payment_terms INTEGER,
    default_payment_terms_type VARCHAR(12),
    default_payment_method_id INTEGER,
    bank_name VARCHAR(255),
    bank_iban VARCHAR(50),
    bank_swift_code VARCHAR(50),
    shipping_address VARCHAR(255),
    e_invoice BOOLEAN,
    ei_code VARCHAR(50),
    has_intent_declaration BOOLEAN,
    intent_declaration_protocol_number VARCHAR(50),
    intent_declaration_protocol_date DATE,
    created_at DATE,
    updated_at DATE,
    FOREIGN KEY(default_vat_id) REFERENCES vat_types(id),
    FOREIGN KEY(default_payment_method_id) REFERENCES payment_methods(id)
);

-- ISSUED DOCUMENTS (INVOICES)
CREATE TABLE issued_documents (
    id INTEGER PRIMARY KEY,
    original_id INTEGER,
    entity_id INTEGER,
    type VARCHAR(14),
    number INTEGER,
    numeration VARCHAR(50),
    year INTEGER,
    currency_id VARCHAR(3),
    language_code VARCHAR(2),
    subject VARCHAR(255),
    visible_subject VARCHAR(255),
    rc_center VARCHAR(50),
    notes TEXT,
    rivalsa FLOAT,
    cassa FLOAT,
    cassa_taxable FLOAT,
    cassa2 FLOAT,
    cassa2_taxable FLOAT,
    global_cassa_taxable FLOAT,
    withholding_tax FLOAT,
    withholding_tax_taxable FLOAT,
    other_withholding_tax FLOAT,
    stamp_duty FLOAT,
    payment_method_id INTEGER,
    use_split_payment BOOLEAN,
    use_gross_prices BOOLEAN,
    e_invoice BOOLEAN,
    show_totals VARCHAR(8),
    show_notification_button BOOLEAN,
    show_tspay_button BOOLEAN,
    delivery_note BOOLEAN,
    accompanying_invoice BOOLEAN,
    amount_net FLOAT,
    amount_vat FLOAT,
    amount_gross FLOAT,
    amount_due_discount FLOAT,
    amount_rivalsa FLOAT,
    amount_withholding_tax FLOAT,
    amount_other_withholding_tax FLOAT,
    created_at DATE,
    updated_at DATE,
    FOREIGN KEY(entity_id) REFERENCES entities(id),
    FOREIGN KEY(currency_id) REFERENCES currencies(id),
    FOREIGN KEY(language_code) REFERENCES languages(code),
    FOREIGN KEY(payment_method_id) REFERENCES payment_methods(id)
);

-- RECEIVED DOCUMENTS
CREATE TABLE received_documents (
    id INTEGER PRIMARY KEY,
    original_id INTEGER,
    entity_id INTEGER,
    type VARCHAR(22),
    number VARCHAR(50),
    year INTEGER,
    currency_id VARCHAR(3),
    language_code VARCHAR(2),
    date DATE,
    duty_stamp_amount FLOAT,
    rc_center VARCHAR(50),
    invoice_number VARCHAR(50),
    is_marked BOOLEAN,
    is_detailed BOOLEAN,
    e_invoice BOOLEAN,
    next_due_date DATE,
    currency_exchange_rate FLOAT,
    attachment_token VARCHAR(255),
    amount_net FLOAT,
    amount_vat FLOAT,
    amount_gross FLOAT,
    amount_withholding_tax FLOAT,
    amount_other_withholding_tax FLOAT,
    created_at DATE,
    updated_at DATE,
    FOREIGN KEY(entity_id) REFERENCES entities(id),
    FOREIGN KEY(currency_id) REFERENCES currencies(id),
    FOREIGN KEY(language_code) REFERENCES languages(code)
);

-- CASHBOOK ENTRIES
CREATE TABLE cashbook_entries (
    id INTEGER PRIMARY KEY,
    original_id INTEGER,
    date DATE,
    amount FLOAT,
    payment_account_id INTEGER,
    kind VARCHAR(20),
    entity_id INTEGER,
    type VARCHAR(50),
    description TEXT,
    FOREIGN KEY(payment_account_id) REFERENCES payment_accounts(id),
    FOREIGN KEY(entity_id) REFERENCES entities(id)
);

-- RECEIPTS
CREATE TABLE receipts (
    id INTEGER PRIMARY KEY,
    original_id INTEGER,
    date DATE,
    number VARCHAR(50),
    numeration VARCHAR(50),
    amount_net FLOAT,
    amount_vat FLOAT,
    amount_gross FLOAT,
    use_gross_prices BOOLEAN,
    entity_id INTEGER,
    type VARCHAR(50),
    description TEXT,
    rc_center VARCHAR(50),
    payment_account_id INTEGER,
    created_at DATE,
    updated_at DATE,
    FOREIGN KEY(entity_id) REFERENCES entities(id),
    FOREIGN KEY(payment_account_id) REFERENCES payment_accounts(id)
);

-- ISSUED DOCUMENT ITEMS
CREATE TABLE issued_document_items (
    id INTEGER PRIMARY KEY,
    original_id INTEGER,
    product_id INTEGER,
    code VARCHAR(50),
    name VARCHAR(255),
    measure VARCHAR(50),
    qty FLOAT,
    net_price FLOAT,
    gross_price FLOAT,
    vat_id INTEGER,
    category VARCHAR(255),
    description TEXT,
    discount FLOAT,
    discount_highlight BOOLEAN,
    not_taxable BOOLEAN,
    apply_withholding_taxes BOOLEAN,
    stock BOOLEAN,
    ei_raw TEXT,
    document_id INTEGER,
    FOREIGN KEY(product_id) REFERENCES products(id),
    FOREIGN KEY(vat_id) REFERENCES vat_types(id),
    FOREIGN KEY(document_id) REFERENCES issued_documents(id)
);

-- RECEIVED DOCUMENT ITEMS
CREATE TABLE received_document_items (
    id INTEGER PRIMARY KEY,
    original_id INTEGER,
    product_id INTEGER,
    code VARCHAR(50),
    name VARCHAR(255),
    measure VARCHAR(50),
    qty FLOAT,
    net_price FLOAT,
    gross_price FLOAT,
    vat_id INTEGER,
    category VARCHAR(255),
    description TEXT,
    discount FLOAT,
    not_taxable BOOLEAN,
    stock BOOLEAN,
    ei_raw TEXT,
    document_id INTEGER,
    FOREIGN KEY(product_id) REFERENCES products(id),
    FOREIGN KEY(vat_id) REFERENCES vat_types(id),
    FOREIGN KEY(document_id) REFERENCES received_documents(id)
);

-- ISSUED DOCUMENT PAYMENTS
CREATE TABLE issued_document_payments (
    id INTEGER PRIMARY KEY,
    original_id INTEGER,
    due_date DATE,
    amount FLOAT,
    status VARCHAR(20),
    payment_account_id INTEGER,
    paid_date DATE,
    ei_raw TEXT,
    document_id INTEGER,
    FOREIGN KEY(payment_account_id) REFERENCES payment_accounts(id),
    FOREIGN KEY(document_id) REFERENCES issued_documents(id)
);

-- RECEIVED DOCUMENT PAYMENTS
CREATE TABLE received_document_payments (
    id INTEGER PRIMARY KEY,
    original_id INTEGER,
    due_date DATE,
    amount FLOAT,
    status VARCHAR(20),
    payment_account_id INTEGER,
    paid_date DATE,
    document_id INTEGER,
    FOREIGN KEY(payment_account_id) REFERENCES payment_accounts(id),
    FOREIGN KEY(document_id) REFERENCES received_documents(id)
);