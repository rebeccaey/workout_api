from uuid import uuid4
from typing import List
from fastapi import APIRouter, Body, HTTPException, Query, status
from pydantic import UUID4
from fastapi_pagination import PaginationParams, Page
from sqlalchemy.exc import IntegrityError
from workout_api.categorias.schemas import CategoriaIn, CategoriaOut
from workout_api.categorias.models import CategoriaModel
from workout_api.contrib.dependencies import DatabaseDependency
from sqlalchemy.future import select

router = APIRouter()

@router.post(
    '/', 
    summary='Criar uma nova Categoria',
    status_code=status.HTTP_201_CREATED,
    response_model=CategoriaOut,
)
async def post(
    db_session: DatabaseDependency, 
    categoria_in: CategoriaIn = Body(...)
) -> CategoriaOut:
    try:
        categoria_out = CategoriaOut(id=str(uuid4()), **categoria_in.model_dump())
        categoria_model = CategoriaModel(**categoria_out.model_dump())
        
        db_session.add(categoria_model)
        await db_session.commit()
        
        return categoria_out
    
    except IntegrityError as e:
        # Verifica se a exceção ocorreu devido a violação de integridade
        if "duplicate key value violates unique constraint" in str(e):
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                detail=f'Já existe uma categoria cadastrada com o nome: {categoria_in.nome}'
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ocorreu um erro ao inserir os dados no banco'
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ocorreu um erro inesperado: {str(e)}'
        )

@router.get(
    '/', 
    summary='Consultar todas as Categorias',
    status_code=status.HTTP_200_OK,
    response_model=Page[CategoriaOut],
)
async def query(
    db_session: DatabaseDependency,
    params: PaginationParams = PaginationParams()
) -> Page[CategoriaOut]:
    query = select(CategoriaModel)
    categorias = await paginate(db_session, query, params=params)
    return categorias

@router.get(
    '/{id}', 
    summary='Consulta uma Categoria pelo id',
    status_code=status.HTTP_200_OK,
    response_model=CategoriaOut,
)
async def get(id: UUID4, db_session: DatabaseDependency) -> CategoriaOut:
    categoria: CategoriaOut = (
        await db_session.execute(select(CategoriaModel).filter_by(id=id))
    ).scalars().first()

    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f'Categoria não encontrada no id: {id}'
        )
    
    return categoria
