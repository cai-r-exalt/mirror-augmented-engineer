# Funcionalidades de la Buvette de Bel'Air

Bienvenido al proyecto La Buvette de Bel'Air! Este documento resume las funcionalidades clave del backend diseñado para gestionar de forma eficiente las bebidas y snacks.

## Funcionalidades

### Como asistente del festival, quiero consultar el saldo restante de mis tokens

Reglas:
- Un asistente tiene dos tipos de tokens: tokens de bebida y tokens de comida
- Un asistente puede tener cero o más tokens de bebida
- Un asistente puede tener cero o más tokens de comida
- Un asistente no puede tener un saldo negativo de tokens
- Un asistente recibe 9 tokens de comida y 6 tokens de bebida por cada día de festival
- Los tokens no gastados no se transfieren al día siguiente

### Como asistente del festival, quiero realizar un pedido de bebida

Reglas:
- Una bebida puede ser alcohólica o no alcohólica
- Una bebida no alcohólica no cuesta tokens de bebida
- Una bebida alcohólica normal cuesta un token de bebida
- Una bebida alcohólica premium cuesta dos tokens de bebida

### Como asistente del festival, quiero realizar un pedido de comida

Reglas:
- Hay dos tipos de artículos alimentarios: snacks y comidas
- Las comidas cuestan 3 tokens de comida
- Los snacks cuestan 1 token de comida

### Como asistente del festival, quiero poder pedir varios artículos en un solo pedido

Reglas:
- Un asistente puede pedir varios artículos en un solo pedido
- El coste total del pedido no debe exceder el saldo de tokens del asistente, ni para tokens de bebida ni para tokens de comida

### Como grupo de asistentes, queremos poder juntar nuestros tokens para realizar un pedido grupal

Reglas:
- El pedido grupal solo puede realizarse si los tokens combinados son suficientes para cubrir el coste total
- Cada asistente puede contribuir cualquier cantidad de sus tokens al pedido grupal
- El pedido grupal se tratará como un único pedido y seguirá las mismas reglas

### Como asistente del festival, quiero poder modificar mi pedido

Reglas:
- Un pedido solo puede modificarse si aún no ha sido reconocido (acknowledged) por el barman
- El asistente puede añadir o eliminar artículos del pedido
- El coste total del pedido modificado no debe exceder el saldo de tokens del asistente (bebida o comida)
- Si el pedido ya ha sido reconocido, se debe notificar al barman de los cambios solicitados

### Como asistente del festival, quiero poder cancelar mi pedido

Reglas:
- Un pedido solo puede cancelarse si aún no ha sido reconocido por el barman
- Al cancelar, los tokens usados para el pedido se reembolsan al saldo del asistente
- El asistente recibe una confirmación de la cancelación

### Como barman, quiero reconocer un pedido para que el asistente sepa que su pedido está en preparación, y proporcionar un tiempo estimado de preparación

Reglas:
- Una vez reconocido un pedido, el asistente es notificado de que su pedido está en preparación
- Se proporciona un tiempo estimado de preparación al asistente en función de la carga y del pedido
- El tiempo estimado de preparación se calcula de la siguiente manera:
  - Para pedidos que contengan solo bebidas no alcohólicas: 1 minuto por tipo de bebida (p. ej. 3 bebidas no alcohólicas diferentes = 3 minutos)
  - Para pedidos que contengan bebidas alcohólicas normales: 2 minutos por bebida
  - Para pedidos que contengan bebidas alcohólicas premium: 3 minutos por bebida
  - Para pedidos mixtos, el tiempo total es la suma de los tiempos para cada tipo (no alcohólicas, alcohólicas normales, alcohólicas premium)
  - Para pedidos que contengan snacks: 2 minutos por tipo de snack
  - Para pedidos que contengan comidas: 10 minutos por tipo de comida más el tiempo de preparación más largo de cualquier bebida en el pedido

La idea es que las comidas tardan más en prepararse, pero pueden prepararse en paralelo con las bebidas.
Los pedidos que contienen el mismo tipo de artículos se preparan juntos, por lo que solo importa el número de tipos diferentes de artículos para el tiempo de preparación.

### Como barman, quiero marcar un pedido como listo para que el asistente sepa que puede recogerlo

Reglas:
- Un pedido solo puede marcarse como listo si hay suficientes artículos preparados para satisfacer el pedido
- Una vez marcado como listo, el asistente es notificado de que puede recoger su pedido

### Como barman, al recibir una solicitud de cambio de un pedido ya reconocido, quiero revisar y aprobar o rechazar los cambios

Reglas:
- La solicitud de cambio solo puede aceptarse si al menos uno de los artículos ya preparados puede transferirse a otro pedido
- Una vez aceptada la solicitud, el asistente es notificado del nuevo tiempo estimado de preparación

### Como asistente del festival, quiero transferir tokens a otro asistente

Reglas:
- El asistente puede transferir hasta tres tokens de cada tipo a otro asistente
- La transferencia de tokens debe ser confirmada por el asistente receptor
- El saldo de tokens del asistente emisor no puede quedar negativo como resultado de la transferencia

### Como barman, quiero que se envíen notificaciones periódicas a los asistentes del festival para recordarles que beban agua, porque hace calor!

Reglas:
- Cada hora, se envía una notificación a todos los asistentes recordándoles que beban agua
- La notificación incluye un mensaje amistoso y fomenta el consumo responsable
- Si un asistente ha consumido más de 3 bebidas alcohólicas en la última hora, la notificación debe enviarse con más frecuencia, cada 30 minutos
- La notificación debe enviarse solo entre las 11:00 y las 19:00 cada día del festival (porque después de las 19:00 es hora de festejar, y antes de las 11:00, con suerte nadie bebe otra cosa que zumos de fruta!)
