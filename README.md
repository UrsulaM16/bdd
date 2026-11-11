# Bases de datos relacionales — apuntes de formación

Material de estudio sobre diseño de bases de datos relacionales. **Este repositorio no es una aplicación ni un proyecto SQL terminado.**

## Contenido

- [Apuntes en Markdown](apuntes_bbdd.md): modelo relacional, diagramas entidad-relación, restricciones, dependencias funcionales, claves y normalización (1FN, 2FN, 3FN y BCNF).
- [Apuntes en PDF](apuntes_bbdd.pdf): versión de lectura del material.
- [`md_to_pdf.py`](md_to_pdf.py): script auxiliar de conversión de Markdown a PDF; su ejecución y dependencias están pendientes de verificar.
- [`ejemplo_consultas.sql`](ejemplo_consultas.sql): ejercicio con dos tablas relacionadas, cinco productos ficticios, consultas `WHERE`, `ORDER BY` e `INNER JOIN`. Probado con SQLite.

## Propósito

Conservar documentación de aprendizaje de programación y bases de datos del itinerario IFCD0112. Los apartados incluyen explicaciones y ejercicios tipo examen con soluciones; **no deben confundirse con un proyecto de base de datos implementado**.

## Cómo probar las consultas

Con `sqlite3` instalado:

```bash
sqlite3 :memory: < ejemplo_consultas.sql
```

La salida muestra tres resultados de consultas. Puedes estudiar las instrucciones antes de ejecutarlas.

## Pendiente de mejorar

- Ampliar el ejemplo SQL con más consultas y pruebas automatizadas.
- Verificar la conversión a PDF y documentar dependencias.
- Revisar las atribuciones y el origen del material docente antes de reutilizarlo en publicaciones.

[Volver al perfil](https://github.com/UrsulaM16)
