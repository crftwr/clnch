#ifndef	__MyDArray
#define	__MyDArray

#include "windows.h"

template<typename T>
class CMyDArray{
	protected:
		typedef	T	_node;
	public:
		class iterator{
			private:
				_node*	_ptr;
			public:
				iterator(){}
				iterator(_node *ptr) : _ptr(ptr){}
				
				iterator& operator++(){
					_ptr++;
					return (*this);
				}
				iterator operator++(int){
					iterator _Tmp = *this;
					++*this;
					return (_Tmp);
				}
				iterator& operator--(){
					_ptr--;
					return (*this);
				}
				iterator operator--(int){
					iterator _Tmp = *this;
					--*this;
					return (_Tmp);
				}
				iterator& operator+=(int _N)
					{_ptr += _N;
					return (*this); }
				iterator& operator-=(int _N)
					{return (*this += -_N); }
				iterator operator+(int _N) const
					{iterator _Tmp = *this;
					return (_Tmp += _N); }
				iterator operator-(int _N) const
					{iterator _Tmp = *this;
					return (_Tmp -= _N); }
				T& operator*(){return *_ptr;}
				//T* operator&(){return _ptr;}
				T* operator->() const
					{return (_ptr); }
				bool operator==(const iterator& x) const
					{return (_ptr == x._ptr); }
				bool operator!=(const iterator& x) const
					{return (!(*this == x)); }
				T* operator[](int _N) const
					{return (*(*this + _N)); }
				_node *node(void){return _ptr;}
		};
	protected:
		_node	*_array;
		int		_maxnum;
	public:
		CMyDArray(){
			_maxnum = 0;
			_array = NULL;
		}
		CMyDArray(int num){
			_array = new T[num];
			_maxnum = (_array) ? num : 0;
		}
		~CMyDArray(){
			clear();
		}
		BOOL allocate(int num){
			clear();
			_array = new T[num];
			if(_array == NULL) return FALSE;
			_maxnum = num;
			return TRUE;
		}
		int max_size(void){
			return	_maxnum;
		}
		int size(void){
			return	_maxnum;
		}
		iterator begin(void){
			return iterator(_array);
		}
		iterator end(void){
			return iterator(_array + _maxnum);
		}
		void clear(){
			delete[] _array;
			_array = NULL;
		}
		T& operator[](int i){
			return (*(begin() + i));
		}
};

#endif
