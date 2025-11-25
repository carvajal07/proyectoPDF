# Análisis de Simplificación del XML de Generación de PDF

## Resumen Ejecutivo

Se ha realizado un análisis exhaustivo del código Python que procesa el XML de configuración de PDFs, identificando **exactamente** qué propiedades y nodos se utilizan realmente. El resultado es un XML simplificado que contiene **solo las propiedades necesarias** para el funcionamiento del sistema.

## Metodología

1. **Análisis del código fuente**: Se revisaron todos los archivos Python en el directorio `PDF-Generator` que leen y procesan el XML
2. **Identificación de accesos**: Se identificaron todos los usos de `.find()`, `.findall()`, `.get()`, `.text`, `.tag`, y `.attrib`
3. **Mapeo de propiedades**: Se mapeó cada propiedad XML a su uso en el código
4. **Generación del XML simplificado**: Se creó un nuevo esquema con solo las propiedades usadas

## Sección 1: Properties del WorkFlow (ELIMINADAS COMPLETAMENTE)

### ❌ **TODAS las Properties se eliminaron**

El XML original contiene **más de 300 propiedades** en la sección `<WorkFlow><Property>` (líneas 3-2071 del XML original).

**Ninguna de estas propiedades se lee en el código Python.**

El código solo procesa la sección `<Layout>` que comienza después de todas las Properties.

### Ejemplos de propiedades eliminadas:
- AFPApplyMediumOrientation
- AFPDefaultCP
- AFPFontDPIDefault
- PDFComplex
- PCLImport-*
- HTMLImport-*
- Y más de 290 propiedades adicionales

**Impacto**: Eliminación de más de **2000 líneas** de XML innecesarias.

---

## Sección 2: Propiedades Comunes a TODOS los Elementos

### ✅ **Propiedades MANTENIDAS** (para elementos con ParentId):

Todos los elementos que tienen `ParentId` (elementos hijo en la jerarquía) **solo necesitan**:

```xml
<Elemento>
  <Id>123</Id>
  <Name>Nombre</Name>
  <ParentId>ParentId</ParentId>
  <IndexInParent>0</IndexInParent>
</Elemento>
```

### ❌ **Propiedades ELIMINADAS** (presentes en el XML original):

- `Comment` - No se lee en el código
- `SecurityDescriptorId` - No se lee en el código
- `Forward` - No se lee en el código

**Impacto**: Reducción de ~30% en cada elemento hijo.

---

## Sección 3: Análisis por Tipo de Elemento

### 📄 **PAGE**

#### ✅ Propiedades MANTENIDAS:
- `Id` - Identificador único
- `Width` - Ancho de página *(process_page.py:56)*
- `Height` - Alto de página *(process_page.py:57)*
- `ConditionType` - Tipo de condición *(process_page.py:60, process_document.py:98)*
- `NextPageId` - Siguiente página *(process_page.py:63)*
- `Pages` (subnodo con SelectionType, FirstPageId, PageCondition, DefaultPageId) *(process_document.py)*

#### ❌ Propiedades ELIMINADAS (40+ propiedades):
- `DynamicHeight`, `DeltaHeight`, `LogicalPageNameType`, `LogicalPageName`, `LogicalPageName2VariableId`, `SheetNameVariableId` (5 veces), `Weight`, `BackgroundColor`, `LogicalPageNameFlowId`, `LogicalPageNameEngine`, `LogicalPageName2FlowId`, `LogicalPageName2Engine`, `SheetNameFlowId`, `SheetNameFlowEngine` (4 pares), `RepeatedById`, `RepeatedIndexId`

**Reducción**: ~85% de las propiedades eliminadas

---

### 🔲 **FLOWAREA**

#### ✅ Propiedades MANTENIDAS:
- `Id`, `Name`, `ParentId`, `IndexInParent` - Básicas
- `Pos` (con atributos X, Y) - Posición *(flowarea_renderer.py:51-52)*
- `Size` (con atributos X, Y) - Tamaño *(flowarea_renderer.py:53-54)*
- `FlowId` - Flujo de contenido *(flowarea_renderer.py:47)*
- `BorderStyleId` - Estilo de borde *(flowarea_renderer.py:48)*
- `FlowingToNextPage` - Flujo a siguiente página *(flowarea_renderer.py:45)*

#### ❌ Propiedades ELIMINADAS (50+ propiedades):
- `Rotation`, `Skew`, `FlipX`, `Scale`, `Transformation_M0-M5`, `IsVisible`, `IsLocked`, `VariablePosXId`, `VariablePosYId`, `PrintState`, `VariablePrintStateId`, `VariableRotId`, `SizeLocked`, `PosLocked`, `ContentLocked`, `StyleLocked`, `RotationPointX`, `RotationPointY`, `RotationRound`, `InfluencedMessages`, `DitheringMode`, `UnitType`, `RunaroundType`, `RunaroundWrapType`, `Margin`, `Invert`, `ForbidStatic`, `NextFlowAreaId`, `BorderType`, `VerticalAligment`, `WritingDirection`, `MiddleEastSupport`, `FittingType`, `BalancingGroup`, `FARunaroundType`, `Path`, `SupplementaryCharSupport`, `DynamicHeight`, `FirstBaseLineType`, `MinFirstLineBasePos`, `AllowEmptyFlowArea`

**Reducción**: ~88% de las propiedades eliminadas

---

### 📝 **FLOW**

#### ✅ Propiedades MANTENIDAS:
- `Id`, `Name`, `ParentId`, `IndexInParent` - Básicas
- `Type` - Tipo de flujo *(flow_renderer.py:42)*
- `FlowContent` - Contenido completo con P, T, O *(flow_renderer.py:46-143)*
- `Condition` (con atributo Value) - Para flujos condicionales *(flow_renderer.py:60)*
- `Default` - Contenido por defecto *(flow_renderer.py:83)*

#### Subelementos procesados dentro de FlowContent:
- `P` (párrafo) con atributo `Id` *(flow_renderer.py:47)*
- `T` (texto) con atributo `Id` *(flow_renderer.py:53)*
- `O` (objeto) con atributo `Id` *(flow_renderer.py:62)*

#### ❌ Propiedades ELIMINADAS (10+ propiedades):
- `DocxLock`, `IsInsertPoint`, `SectionFlow`, `TriggerBefore`, `TriggerInside`, `TriggerAfter`, `FlowUsageLogging`

**Reducción**: ~70% de las propiedades eliminadas

---

### 📊 **TABLE**

#### ✅ Propiedades MANTENIDAS:
- `Id`, `Name`, `ParentId`, `IndexInParent` - Básicas
- `BordersType` - Tipo de bordes *(table_renderer.py:42)*
- `HorizontalCellSpacing` - Espaciado horizontal *(table_renderer.py:43)*
- `VerticalCellSpacing` - Espaciado vertical *(table_renderer.py:44)*
- `TableAlignment` - Alineación *(table_renderer.py:45)*
- `ColumnWidths` (múltiples) con PercentWidth y MinWidth *(table_renderer.py:49-59)*
- `RowSetId` - RowSet raíz *(table_renderer.py:65)*
- `RowSetType`, `SubRowId`, `VariableId` - Usados al procesar *(table_renderer.py:66-91)*
- `RowSetCondition` con Condition *(table_renderer.py:76)*

#### ❌ Propiedades ELIMINADAS (20+ propiedades):
- `MinWidth`, `MaxWidth`, `PercentWidth` (del Table, no de ColumnWidths), `SpaceLeft`, `SpaceTop`, `SpaceRight`, `SpaceBottom`, `IncludeLineGap`, `UseColumnWidths`, `HTMLFormatting`, `DisplayAsImage`, `TableStyleId`, `EnableById` (4 veces), `ResponsiveHtml`, `Editability`, `IsHeader` (4 veces), `RelativeFill`

**Reducción**: ~65% de las propiedades eliminadas

---

### 🔢 **ROWSET**

#### ✅ Propiedades MANTENIDAS:
- `Id`, `Name`, `ParentId`, `IndexInParent` - Básicas
- `RowSetType` - Tipo *(rowset_renderer.py:22)*
- `RowSetCondition` con Condition *(rowset_renderer.py:28)*
- `SubRowId` (múltiples) *(rowset_renderer.py:34, 48)*
- `MinHeight` - Altura mínima *(rowset_renderer.py:70)*
- `CellVerticalAlignment` - Alineación *(rowset_renderer.py:71)*
- `BorderId` - Borde *(rowset_renderer.py:72)*

#### ❌ Propiedades ELIMINADAS:
Generalmente los RowSet en el XML original solo tienen propiedades básicas en la versión con ParentId.

**Reducción**: Mínima, ya que no había muchas propiedades adicionales

---

### 📦 **CELL**

#### ✅ Propiedades MANTENIDAS:
- `Id`, `Name`, `ParentId`, `IndexInParent` - Básicas
- `FlowId` - Flujo de contenido *(cell_renderer.py:23)*
- `BorderId` - Borde *(cell_renderer.py:24)*

#### ❌ Propiedades ELIMINADAS:
Similar a RowSet, las celdas tienen estructura simple.

**Reducción**: Mínima

---

### 🔤 **FONT**

#### ✅ Propiedades MANTENIDAS:
- `Id` (con atributo Name) - Identificador
- `Name` - Nombre de la fuente
- `FontName` - Nombre interno *(fonts.py:17)*
- `SubFont` (múltiples) con atributo Name *(fonts.py:18-24)*
  - `FontLocation` - Ubicación del archivo *(fonts.py:23)*

#### ❌ Propiedades ELIMINADAS (dentro de SubFont):
- `FontIndex`, `OpenFontFileFlag`, `Bold`, `Italic`

**Reducción**: ~50% de las propiedades de SubFont eliminadas

---

### 🎨 **COLOR**

#### ✅ Propiedades MANTENIDAS:
- `Id`, `Name`, `ParentId`, `IndexInParent` - Básicas
- `RGB` - Valores RGB *(colors.py:16)*

#### ❌ Propiedades ELIMINADAS (9 propiedades):
- `CMYK`, `LAB`, `HSB`, `SpotColor`, `OverwriteSpotColor`, `SeparationColorSpace`, `Density`, `IsDeviceN`, `IsInherit`, `ColorType`

**Reducción**: ~90% de las propiedades eliminadas

---

### 📐 **BORDERSTYLE**

#### ✅ Propiedades MANTENIDAS:
- `Id`, `Name`, `ParentId`, `IndexInParent` - Básicas
- `ColorId` - Color del borde *(border_renderer.py:33, borderstyles.py:24)*
- `TopLine`, `BottomLine`, `LeftLine`, `RightLine` - Líneas *(border_renderer.py:41-68)*
  - `FillStyle` - Estilo de relleno *(borderstyles.py:37)*
  - `LineWidth` - Ancho *(border_renderer.py:49, borderstyles.py:38)*
- `LeftRightLine`, `RightLeftLine` - Diagonales *(border_renderer.py:70-76)*
- `UpperLeftCorner`, `RightTopCorner`, `LowerRightCorner`, `LowerLeftCorner` - Esquinas *(border_renderer.py:79-104)*
- `UpperLeftCornerType`, `UpperRightCornerType`, `LowerRightCornerType`, `LowerLeftCornerType` *(border_renderer.py:106-136)*
  - `CornerRadius` (atributos X, Y) *(border_renderer.py:131)*
- `FillStyleId` - Relleno *(border_renderer.py:138)*

#### ❌ Propiedades ELIMINADAS (15+ propiedades):
- `ShadowStyleId`, `Margin`, `Offset`, `ShadowOffset`, `JoinType`, `Miter`, `CapType` (dentro de cada línea), `LineStyle` (dentro de cada línea), `CornerType` (dentro de cada tipo de esquina), `Type`

**Reducción**: ~60% de las propiedades eliminadas

---

### 📄 **PARASTYLE** (Estilo de Párrafo)

#### ✅ Propiedades MANTENIDAS:
- `Id` (con atributo Name)
- `AncestorId` - Estilo padre *(flow_renderer.py:133)*
- `LeftIndent` - Sangría izquierda *(parastyles.py:16)*
- `RightIndent` - Sangría derecha *(parastyles.py:17)*
- `FirstLineLeftIndent` - Sangría primera línea *(parastyles.py:18)*
- `SpaceBefore` - Espacio antes *(parastyles.py:19)*
- `SpaceAfter` - Espacio después *(parastyles.py:20)*
- `LineSpacing` - Espaciado *(parastyles.py:21)*
- `Widow` - Control de viudas *(parastyles.py:22)*
- `Orphan` - Control de huérfanas *(parastyles.py:23)*
- `KeepWithNext` - Mantener con siguiente *(parastyles.py:24)*
- `KeepLinesTogether` - Mantener líneas juntas *(parastyles.py:25)*
- `DontWrap` - No envolver *(parastyles.py:26)*
- `HAlign` - Alineación horizontal *(parastyles.py:27)*

#### ❌ Propiedades ELIMINADAS (30+ propiedades):
- `LineSpacingType`, `DefaultTextStyleId`, `NextParagraphStyleId`, `BorderStyleId`, `NewAreaPageAfter`, `IsVisible`, `ConnectBorders`, `WithLineGap`, `BullettingId`, `IgnoreEmptyLines`, `TabulatorProperties`, `Hyphenation`, `NumberingType`, `NumberingVariableId`, `NumberingFrom`, `SpaceBeforeFirst`, `KeepWithPrevious`, `RightReadingOrder`, `Reversed`, `CutFreely`, `CalcMaxSpaceBeforeAfter`, `NewAreaPageBefore`, `DistributeLineSpace`, `Type`, `Css`

**Reducción**: ~70% de las propiedades eliminadas

---

### 🔡 **TEXTSTYLE** (Estilo de Texto)

#### ✅ Propiedades MANTENIDAS:
- `Id` (con atributo Name)
- `AncestorId` - Estilo padre *(flow_renderer.py:121)*
- `FontSize` - Tamaño *(flow_renderer.py:86)*
- `FillStyleId` - Color *(flow_renderer.py:87)*
- `FontId` - Fuente *(flow_renderer.py:88)*
- `SubFont` - Variante *(flow_renderer.py:89)*
- `UsePercentDecent`, `PercentFontDecent`, `PointFontDecent` - Font-fitting *(flow_renderer.py:126-130)*
- `IterationCount` - Iteraciones de font-fitting *(flow_renderer.py:125)*

#### ❌ Propiedades ELIMINADAS (40+ propiedades):
- `LineWidth`, `MiterLimit`, `BaselineShift`, `InterCharacterSpacing`, `OutlineStyleId`, `CapType`, `JoinType`, `Kerning`, `BorderStyleId`, `IsVisible`, `ConnectBorders`, `WithLineGap`, `Bold`, `Italic`, `Underline`, `Strikethrough`, `Language`, `SmallCap`, `SuperScript`, `SubScript`, `SuperScriptOffset`, `SubScriptOffset`, `SuperSubScriptSize`, `AffectSuperSubScriptUnderline`, `AffectSuperSubScriptStrikethrough`, `SmallCapSize`, `CustomUnderlineStrikethrough`, `UnderlineOffset`, `UnderlineWidth`, `StrikethroughOffset`, `StrikethroughWidth`, `URLLink`, `HorizontalScale`, `WrappingRuleId`, `Type`, `UnderlineLineStyleId`, `StrikethroughLineStyleId`, `ShadowStyleId`, `ShadowStyleOffset`, `IsFixedWidth`, `FixedWidth`, `Css`

**Reducción**: ~85% de las propiedades eliminadas

---

### 🖼️ **IMAGE**

#### ✅ Propiedades MANTENIDAS:
- `Id`, `Name`, `ParentId`, `IndexInParent` - Básicas
- `ImageType` - Tipo *(image_renderer.py:44, images.py:17)*
- `ImageLocation` - Ubicación *(image_renderer.py:64, images.py:20)*
- `VariableId` - Variable con datos *(image_renderer.py:58, images.py:18)*

#### ❌ Propiedades ELIMINADAS:
Las imágenes con ParentId tienen solo propiedades básicas.

**Reducción**: Mínima

---

### 🖼️ **IMAGEOBJECT**

#### ✅ Propiedades MANTENIDAS:
- `Id`, `Name`, `ParentId`, `IndexInParent` - Básicas
- `Pos` (atributos X, Y) - Posición *(image_renderer.py:41-42)*
- `Size` (atributos X, Y) - Tamaño *(image_renderer.py:43-44)*
- `Transformation_M0` a `M5` - Transformaciones *(image_renderer.py:49-54)*
- `ImageId` - ID de la imagen *(process_elements.py:48)*
- `ImageType`, `VariableId`, `ImageLocation` - Del Image referenciado

#### ❌ Propiedades ELIMINADAS:
Similar a FlowArea, se eliminan todas las propiedades de layout no usadas.

**Reducción**: ~80%

---

### 📐 **PATHOBJECT** (Figuras Vectoriales)

#### ✅ Propiedades MANTENIDAS:
- `Id`, `Name`, `ParentId`, `IndexInParent` - Básicas
- `Pos` (atributos X, Y) *(path_renderer.py:91-92)*
- `Size` (atributos X, Y) *(path_renderer.py:89-90)*
- `Scale` (atributos X, Y) *(path_renderer.py:32-33)*
- `Transformation_M0` a `M5` *(path_renderer.py:35-40)*
- `Path` con subelementos *(path_renderer.py:42)*:
  - `MoveTo` (atributos X, Y) *(path_renderer.py:45)*
  - `LineTo` (atributos X, Y) *(path_renderer.py:49)*
  - `BezierTo` (atributos X1, Y1, X2, Y2, X, Y) *(path_renderer.py:53)*
  - `ArcTo` (atributos X, Y) *(path_renderer.py:83)*
  - `ClosePath` *(path_renderer.py:86)*
- `FillStyleId` - Relleno *(path_renderer.py:94)*

#### ❌ Propiedades ELIMINADAS:
Similar a otros objetos gráficos.

**Reducción**: ~75%

---

### 📊 **BARCODE**

#### ✅ Propiedades MANTENIDAS:
- `Id`, `Name`, `ParentId`, `IndexInParent` - Básicas
- `Pos` (atributos X, Y) *(barcode_renderer.py:38-39)*
- `Size` (atributos X, Y) *(barcode_renderer.py:40-41)*
- `Transformation_M0` a `M5` *(barcode_renderer.py:43-48)*
- `VariableId` - Contenido *(barcode_renderer.py:33)*
- `FillStyleId` - Color *(barcode_renderer.py:34)*
- `BarcodeGenerator` *(barcode_renderer.py:51)*:
  - `Type` - Tipo de código *(barcode_renderer.py:52)*
  - `ErrorLevel` - Nivel de error *(barcode_renderer.py:56)*
  - `ModulWidth` - Ancho del módulo *(barcode_renderer.py:61)*
  - `ModulSize` - Tamaño del módulo *(barcode_renderer.py:67)*
  - `Height` - Altura *(barcode_renderer.py:73)*

#### ❌ Propiedades ELIMINADAS:
Propiedades de layout no usadas.

**Reducción**: ~70%

---

### 📈 **CHART**

#### ✅ Propiedades MANTENIDAS:
- `Id`, `Name`, `ParentId`, `IndexInParent` - Básicas
- `Pos` (atributos X, Y) *(chart_renderer.py:32-33)*
- `Size` (atributos X, Y) *(chart_renderer.py:34-35)*
- `Chart_Type` - Tipo de gráfico *(chart_renderer.py:38)*
- `Chart_Title` - Título *(chart_renderer.py:39)*
- `Serie` con `SerieItem` *(chart_renderer.py:44)*:
  - `Value` - Valor *(chart_renderer.py:46)*
  - `Label` - Etiqueta *(chart_renderer.py:47)*

#### ❌ Propiedades ELIMINADAS:
Propiedades de configuración avanzada de gráficos.

**Reducción**: ~60%

---

## Sección 4: Transformaciones y Datos JSON

### ✅ **Nodos MANTENIDOS en json_parser.py**:

El parser de JSON también procesa transformaciones y cruces de datos del XML:

- `CreatedNodes` con atributos: `LinkedType`, `FieldDotName`, `Type`, `DefaultValue`, `ParentDotName`, `LinkedToDotName`, `Operation`
- `Transformations` con:
  - `FCVClassName` - Clase de transformación
  - `FCVProps` - Propiedades de la transformación
  - `Type`, `PreString`, `PostString`, `CaseType` - Para transformaciones específicas
  - `InDecimalSeparator`, `OutDecimalSeparator`, `OutGroupSeparator` - Para ConvNumFCV
- `WorkFlowDefinition` con atributos: `Name`, `Type`, `Optionality`
- `SelectedNodeA`, `SelectedNodeB` con `FullPathName`
- `From`, `FromIndex`, `To`, `ToIndex` - Para conexiones
- `Field` con atributos `Key`, `Value`

**Nota**: Estas secciones no estaban presentes en los XMLs de ejemplo analizados, pero el código las soporta.

---

## Sección 5: Resumen de Impacto

### 📊 Reducción Global Estimada

| Sección | Propiedades Originales | Propiedades Simplificadas | Reducción |
|---------|------------------------|---------------------------|-----------|
| WorkFlow Properties | ~300 | 0 | **100%** |
| Page | ~40 | 6 principales | **85%** |
| FlowArea | ~50 | 6 principales | **88%** |
| Flow | ~10 | 3 principales | **70%** |
| Table | ~25 | 9 principales | **65%** |
| Color | ~10 | 1 (RGB) | **90%** |
| Font | ~15 (por SubFont) | 3 | **80%** |
| BorderStyle | ~35 | 14 | **60%** |
| ParaStyle | ~45 | 14 | **70%** |
| TextStyle | ~50 | 8 | **85%** |
| PathObject | ~30 | 7 principales | **75%** |
| Barcode | ~25 | 8 principales | **70%** |
| Chart | ~20 | 6 principales | **70%** |

### 💾 **Impacto en Tamaño de Archivo**

Basado en el análisis del XML `Colsubsidio_Compose_FacturasWS.xml`:

- **Tamaño Original**: 17,104 líneas
- **Sección Properties**: ~2,071 líneas (12% del total) - **100% eliminable**
- **Propiedades redundantes en elementos**: ~40-50% de las líneas restantes

**Estimación de reducción total**: **50-60% del tamaño del archivo**

---

## Sección 6: Beneficios de la Simplificación

### ✅ **Ventajas**:

1. **Rendimiento**:
   - Menor uso de memoria al cargar XML
   - Parsing más rápido (menos nodos a procesar)

2. **Mantenibilidad**:
   - XML más legible y comprensible
   - Fácil identificación de propiedades relevantes
   - Menos confusión al crear nuevos layouts

3. **Almacenamiento**:
   - Menor espacio en disco
   - Menor espacio en base de datos (tabla SchemeXml)
   - Backups más pequeños

4. **Desarrollo**:
   - Documentación más clara
   - Validación de esquemas más simple
   - Debugging más fácil

### ⚠️ **Consideraciones**:

1. **Compatibilidad**: El XML simplificado NO es compatible con el software Inspire Designer original (que genera estos XMLs)

2. **Migración**: Si se desea usar el XML simplificado, se debe:
   - Convertir todos los XMLs existentes al nuevo formato
   - Asegurar que no haya código legacy que lea propiedades eliminadas
   - Actualizar documentación

3. **Funcionalidad futura**: Si en el futuro se necesita procesar alguna propiedad actualmente eliminada, habrá que agregarla de nuevo

---

## Sección 7: Recomendaciones

### 🎯 **Estrategia Recomendada**:

1. **Mantener ambos formatos** (al menos temporalmente):
   - XML completo para compatibilidad con Inspire Designer
   - XML simplificado para procesamiento interno

2. **Crear herramienta de conversión**:
   - Script que convierte XML completo → XML simplificado
   - Validar que no se pierda información crítica

3. **Implementación gradual**:
   - Probar primero con layouts no críticos
   - Validar que los PDFs generados sean idénticos
   - Expandir a todos los layouts

4. **Documentar diferencias**:
   - Mantener este documento actualizado
   - Documentar cualquier propiedad que se agregue en el futuro

### 📝 **Próximos Pasos**:

1. ✅ **Completado**: Análisis de código y creación de XML simplificado
2. **Siguiente**: Crear script de conversión automática
3. **Siguiente**: Pruebas exhaustivas con PDFs existentes
4. **Siguiente**: Migración gradual de layouts a formato simplificado

---

## Apéndice A: Archivos Analizados

### Código Python Revisado:

1. `/PDF-Generator/pdf/process_document.py`
2. `/PDF-Generator/pdf/process_page.py`
3. `/PDF-Generator/pdf/process_elements.py`
4. `/PDF-Generator/parser/xml_parser.py`
5. `/PDF-Generator/renderer/flowarea_renderer.py`
6. `/PDF-Generator/renderer/flow_renderer.py`
7. `/PDF-Generator/renderer/table_renderer.py`
8. `/PDF-Generator/renderer/rowset_renderer.py`
9. `/PDF-Generator/renderer/cell_renderer.py`
10. `/PDF-Generator/renderer/border_renderer.py`
11. `/PDF-Generator/renderer/path_renderer.py`
12. `/PDF-Generator/renderer/image_renderer.py`
13. `/PDF-Generator/renderer/chart_renderer.py`
14. `/PDF-Generator/renderer/barcode_renderer.py`
15. `/PDF-Generator/styles/fonts.py`
16. `/PDF-Generator/styles/colors.py`
17. `/PDF-Generator/styles/parastyles.py`
18. `/PDF-Generator/styles/borderstyles.py`
19. `/PDF-Generator/styles/images.py`
20. `/PDF-Generator/loader/input_loader.py`
21. `/PDF-Generator/loader/preprocessing.py`
22. `/PDF-Generator/parser/json_parser.py`
23. `/PDF-Generator/transformer/created_nodes.py`
24. `/PDF-Generator/interface/cli.py`

### XML de Referencia:

- `Colsubsidio_Compose_FacturasWS.xml` (17,104 líneas)

---

## Apéndice B: Lista Completa de Atributos XML Usados

### Atributos en elementos (vía .get()):
- `Caption`, `DefaultValue`, `DotName`, `FieldDotName`, `FullPathName`, `Id`, `Key`, `LinkedToDotName`, `LinkedToDotName2`, `LinkedType`, `Name`, `NodeLink2NodeType`, `Operation`, `Optionality`, `ParentDotName`, `SearchArrayKeyValue`, `Type`, `Value`, `X`, `X1`, `X2`, `Y`, `Y1`, `Y2`

### Nodos buscados (vía .find()/.findall()):
- `AncestorId`, `ArcTo`, `BarcodeGenerator`, `BorderId`, `BorderStyleId`, `BordersType`, `BottomLine`, `BezierTo`, `CaseType`, `CellVerticalAlignment`, `Chart_Title`, `Chart_Type`, `ClosePath`, `Color`, `ColorId`, `ColumnWidths`, `Condition`, `ConditionId`, `ConditionType`, `CornerRadius`, `CreatedNodes`, `Default`, `DefaultPageId`, `DontWrap`, `ErrorLevel`, `FCVClassName`, `FCVProps`, `Field`, `FillStyle`, `FillStyleId`, `FirstLineLeftIndent`, `FirstPageId`, `FlowContent`, `FlowId`, `FlowingToNextPage`, `Font`, `FontId`, `FontLocation`, `FontName`, `FontSize`, `From`, `FromIndex`, `HAlign`, `Height`, `HorizontalCellSpacing`, `Id`, `ImageId`, `ImageLocation`, `ImageType`, `IterationCount`, `KeepLinesTogether`, `KeepWithNext`, `Label`, `Layout`, `LeftIndent`, `LeftLine`, `LeftRightLine`, `LineTo`, `LineSpacing`, `LineWidth`, `LowerLeftCorner`, `LowerLeftCornerType`, `LowerRightCorner`, `LowerRightCornerType`, `MinHeight`, `MinWidth`, `ModulSize`, `ModulWidth`, `MoveTo`, `Name`, `NextPageId`, `O`, `Orphan`, `P`, `PageCondition`, `PageId`, `Pages`, `ParentId`, `Path`, `PercentFontDecent`, `PercentWidth`, `PointFontDecent`, `Pos`, `RGB`, `RightIndent`, `RightLeftLine`, `RightLine`, `RightTopCorner`, `RowSetCondition`, `RowSetId`, `RowSetType`, `Scale`, `SelectionType`, `Serie`, `SerieItem`, `Size`, `SpaceAfter`, `SpaceBefore`, `SubFont`, `SubRowId`, `T`, `TableAlignment`, `To`, `ToIndex`, `TopLine`, `Transformation_M0`, `Transformation_M1`, `Transformation_M2`, `Transformation_M3`, `Transformation_M4`, `Transformation_M5`, `Type`, `UpperLeftCorner`, `UpperLeftCornerType`, `UpperRightCornerType`, `UsePercentDecent`, `Value`, `VariableId`, `VerticalCellSpacing`, `Widow`, `Width`, `WorkFlowDefinition`

---

**Fecha de Análisis**: 2025-11-25
**Versión del Código**: Actual (Git commit: be2d287)
**Analista**: Claude Code Assistant
