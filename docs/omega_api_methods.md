# Omega API Methods

﻿﻿﻿﻿﻿﻿﻿﻿Документ подготовлен на основе Swagger Omega API (версия от 16.08.2025). Перечислены основные публичные методы и их назначение. Параметр `Key` во всех методах — это токен из запроса к `/public/api/v1.0/profile/account`.

## Profile
- **POST** `/public/api/v1.0/profile/account`  
  Получение информации об аккаунте и генерация `Data.Key` (сеансового токена).

## Product
- **POST** `/public/api/v1.0/product/search`  
  Поиск товара по фразе. Параметры: `SearchPhrase` (строка), `Rest` (булево), `From` (int), `Count` (int), `Key`.

- **POST** `/public/api/v1.0/product/searchBrand`  
  Поиск по коду и бренду. Параметры: `Code` (строка), `Brand` (строка), `Key`.

- **POST** `/public/api/v1.0/product/searchBrandById`  
  Поиск по коду и ID бренда. Параметры: `Code`, `BrandId`, `Key`.

- **POST** `/public/api/v1.0/product/searchProductIdList`  
  Поиск по списку ID товаров. Параметры: `ProductIdList` (массив чисел), `Key`.

- **POST** `/public/api/v1.0/product/searchProductCardList`  
  Поиск по списку карточек товаров (структуры с артикулами/брендами). Параметры: `ProductCardList` (массив объектов), `Key`.

- **POST** `/public/api/v1.0/product/details`  
  Получение подробной информации по товару/товарам. Параметры: `ProductIdList`, `Key`.

- **POST** `/public/api/v1.0/product/imagesInfo`  
  Список метаданных изображений для товара. Параметры: `ProductId`, `Key`.

- **POST** `/public/api/v1.0/product/image`  
  Получение изображения товара. Параметры: `ProductId`, `Key`.

## Basket (корзина)
- **POST** `/public/api/v1.0/basket/addProduct`  
  Добавление или изменение количества товара в корзине.

- **POST** `/public/api/v1.0/basket/addProductList`  
  Добавление списка товаров в корзину.

- **POST** `/public/api/v1.0/basket/removeProductFromBasket`  
  Удаление товара из корзины.

*(В Swagger есть и другие методы корзины, например очистка корзины или оформление заказа, которые аналогично требуют параметр `Key`.)*

## Order
- **POST** `/public/api/v1.0/order/create`  
  Создание заказа на основе содержимого корзины.

- **POST** `/public/api/v1.0/order/list`  
  Получение списка заказов.

- **POST** `/public/api/v1.0/order/get`  
  Получение информации о конкретном заказе.

## Cross
- **POST** `/public/api/v1.0/cross/get`  
  Получение списка замен (кроссов) для заданного артикула и бренда. Параметры: `Brand`, `Article`, `Key`.

## Reference (справочники)
- **POST** `/public/api/v1.0/reference/country` – список стран.  
- **POST** `/public/api/v1.0/reference/currency` – список валют.  
- **POST** `/public/api/v1.0/reference/brand` – список брендов.

## Delivery and Payment
- **POST** `/public/api/v1.0/delivery/list` – доступные способы доставки.  
- **POST** `/public/api/v1.0/payment/list` – доступные методы оплаты.

## Balance and Messages
- **POST** `/public/api/v1.0/balance/get` – текущий баланс.  
- **POST** `/public/api/v1.0/message/list` – список сообщений.  
- **POST** `/public/api/v1.0/message/get` – просмотр одного сообщения.

> **Примечание:** это краткий перечень основных публичных методов. Полный список можно найти в PDF‑файле Swagger API; в нём около 80 страниц с разными категориями (корзина, цены, заказы, уведомления и пр.). Все запросы требуют указания параметра `Key` и подчиняются лимитам: 30 запросов в минуту и 300 запросов в час【437756488164343†L1-L3】
