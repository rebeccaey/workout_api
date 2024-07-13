from uuid import uuid4
from typing import List
from fastapi import APIRouter, Body, HTTPException, Query, status
from pydantic import UUID4
from fastapi_pagination import PaginationParams, Page
from sqlalchemy.exc import IntegrityError
from workout_api.centro_treinamento.schemas import CentroTreinamentoIn, CentroTreinamentoOut
from workout_api.centro_treinamento.models import CentroTreinamentoModel
from workout_api.contrib.dependencies import DatabaseDependency
from sqlalchemy.future import select

router = APIRouter()

@router.post(
    '/', 
    summary='Criar um novo Centro de treinamento',
    status_code=status.HTTP_201_CREATED,
    response_model=CentroTreinamentoOut,
)
async def post(
    db_session: DatabaseDependency, 
    centro_treinamento_in: CentroTreinamentoIn = Body(...)
) -> CentroTreinamentoOut:
    try:
        centro_treinamento_out = CentroTreinamentoOut(id=str(uuid4()), **centro_treinamento_in.model_dump())
        centro_treinamento_model = CentroTreinamentoModel(**centro_treinamento_out.model_dump())
        
        db_session.add(centro_treinamento_model)
        await db_session.commit()
        
        return centro_treinamento_out
    
    except IntegrityError as e:
        # Verifica se a exceção ocorreu devido a violação de integridade (exemplo: nome duplicado)
        if "duplicate key value violates unique constraint" in str(e):
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                detail=f'Já existe um centro de treinamento cadastrado com o nome: {centro_treinamento_in.nome}'
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
    summary='Consultar todos os centros de treinamento',
    status_code=status.HTTP_200_OK,
    response_model=Page[CentroTreinamentoOut],
)
async def query(
    db_session: DatabaseDependency,
    params: PaginationParams = PaginationParams()
) -> Page[CentroTreinamentoOut]:
    query = select(CentroTreinamentoModel)
    centros_treinamento = await paginate(db_session, query, params=params)
    return centros_treinamento

@router.get(
    '/{id}', 
    summary='Consulta um centro de treinamento pelo id',
    status_code=status.HTTP_200_OK,
    response_model=CentroTreinamentoOut,
)
async def get(id: UUID4, db_session: DatabaseDependency) -> CentroTreinamentoOut:
    centro_treinamento_out: CentroTreinamentoOut = (
        await db_session.execute(select(CentroTreinamentoModel).filter_by(id=id))
    ).scalars().first()

    if not centro_treinamento_out:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f'Centro de treinamento não encontrado no id: {id}'
        )
    
    return centro_treinamento_out
